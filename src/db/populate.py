import asyncio
import re
from typing import List, Dict
from pathlib import Path

import pandas as pd
from sqlalchemy import insert, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from tqdm import tqdm

from src.core.config import settings
from src.models import (
    Movie,
    Genre,
    Star,
    Director,
    Certification,
)
from src.models.accounts import UserGroup, UserGroupEnum
from src.db.session import get_db

CHUNK_SIZE = 1000
CSV_FILE_PATH = str(Path(settings.BASE_DIR) / "db/seed_data/imdb_top_1000.csv")


class CSVDatabaseSeeder:
    """
    A class responsible for seeding the database from a CSV file containing IMDB top movies.
    """

    def __init__(self, csv_file_path: str, db_session: AsyncSession) -> None:
        """
        Initialize the seeder with the path to the CSV file and an async database session.

        :param csv_file_path: The path to the CSV file containing movie data.
        :param db_session: An instance of AsyncSession for performing database operations.
        """
        self._csv_file_path = csv_file_path
        self._db_session = db_session

    async def is_db_populated(self) -> bool:
        """
        Check if the Movie table has at least one record.

        :return: True if there's already at least one movie in the database, otherwise False.
        """
        result = await self._db_session.execute(select(Movie).limit(1))
        first_movie = result.scalars().first()
        return first_movie is not None

    def _preprocess_csv(self) -> pd.DataFrame:
        """
        Load the CSV and clean up data for database insertion.

        :return: A Pandas DataFrame containing cleaned movie data.
        """
        data = pd.read_csv(self._csv_file_path)
        
        data = data.drop_duplicates(subset=['Series_Title', 'Released_Year'], keep='first')
        
        data['Overview'] = data['Overview'].fillna('No overview available')
        data['Meta_score'] = pd.to_numeric(data['Meta_score'], errors='coerce')
        data['Gross'] = data['Gross'].fillna('0')
        
        data['Runtime'] = data['Runtime'].str.extract(r'(\d+)').astype(int)
        data['Gross'] = data['Gross'].str.replace(',', '').astype(float)
        
        print("CSV file preprocessed successfully.")
        return data

    async def _seed_user_groups(self) -> None:
        """
        Seed the UserGroup table with default user groups if none exist.
        """
        count_stmt = select(func.count(UserGroup.id))
        result = await self._db_session.execute(count_stmt)
        existing_groups = result.scalar()

        if existing_groups == 0:
            groups = [{"name": group.value} for group in UserGroupEnum]
            await self._db_session.execute(insert(UserGroup).values(groups))
            await self._db_session.flush()
            print("User groups seeded successfully.")

    async def _get_or_create_bulk(
            self,
            model,
            items: List[str],
            unique_field: str
    ) -> Dict[str, object]:
        """
        For a given model and a list of item names, retrieves existing records
        and creates missing ones in bulk.

        :param model: The SQLAlchemy model class (e.g., Genre, Director, Star).
        :param items: A list of string values to create or retrieve.
        :param unique_field: The field name that should be unique (e.g., "name").
        :return: A dict mapping each item to its model instance.
        """
        if not items:
            return {}

        existing_dict: Dict[str, object] = {}
        items = [item for item in items if item and item.strip()]

        for i in range(0, len(items), CHUNK_SIZE):
            chunk = items[i: i + CHUNK_SIZE]
            result = await self._db_session.execute(
                select(model).where(getattr(model, unique_field).in_(chunk))
            )
            for obj in result.scalars().all():
                key = getattr(obj, unique_field)
                existing_dict[key] = obj

        new_items = [item for item in items if item not in existing_dict]
        new_records = [{unique_field: item} for item in new_items]

        if new_records:
            for i in range(0, len(new_records), CHUNK_SIZE):
                chunk = new_records[i: i + CHUNK_SIZE]
                await self._db_session.execute(insert(model).values(chunk))
                await self._db_session.flush()

            for i in range(0, len(new_items), CHUNK_SIZE):
                chunk = new_items[i: i + CHUNK_SIZE]
                result_new = await self._db_session.execute(
                    select(model).where(getattr(model, unique_field).in_(chunk))
                )
                for obj in result_new.scalars().all():
                    key = getattr(obj, unique_field)
                    existing_dict[key] = obj

        return existing_dict

    def _extract_runtime_minutes(self, runtime_str: str) -> int:
        """Extract integer minutes from runtime string like '142 min'."""
        match = re.search(r'(\d+)', str(runtime_str))
        return int(match.group(1)) if match else 0

    async def _prepare_reference_data(
            self,
            data: pd.DataFrame
    ) -> tuple[Dict[str, object], Dict[str, object], Dict[str, object], Dict[str, object]]:
        """
        Gather unique values for genres, directors, and stars from the DataFrame.

        :param data: The preprocessed Pandas DataFrame.
        :return: A tuple of four dictionaries: (genre_map, director_map, star_map, certification_map).
        """
        genres = {
            genre.strip()
            for genres_str in data['Genre'].dropna() 
            for genre in genres_str.split(',')
            if genre.strip()
        }

        directors = set(data['Director'].dropna().unique())
        directors = {d.strip() for d in directors if d.strip()}

        stars = set()
        for star_col in ['Star1', 'Star2', 'Star3', 'Star4']:
            if star_col in data.columns:
                stars.update(data[star_col].dropna().unique())
        stars = {s.strip() for s in stars if s.strip()}

        certifications = set(data['Certificate'].dropna().unique())
        certifications = {c.strip() for c in certifications if c.strip()}

        return (
            await self._get_or_create_bulk(Genre, list(genres), 'name'),
            await self._get_or_create_bulk(Director, list(directors), 'name'),
            await self._get_or_create_bulk(Star, list(stars), 'name'),
            await self._get_or_create_bulk(Certification, list(certifications), 'name'),
        )

    async def _prepare_movies_data(
            self,
            data: pd.DataFrame,
            certification_map: Dict[str, object]
    ) -> List[Dict[str, object]]:
        """
        Build a list of dictionaries representing movie records.

        :param data: The preprocessed DataFrame.
        :param certification_map: A mapping of certification names to Certification instances.
        :return: A list of dictionaries, each representing a movie record.
        """
        movies_data: List[Dict[str, object]] = []
        
        for _, row in tqdm(data.iterrows(), total=data.shape[0], desc="Processing movies"):
            cert_name = str(row['Certificate']).strip()
            certification = certification_map.get(cert_name)
            
            if not certification:
                continue

            movie = {
                "name": str(row['Series_Title']).strip(),
                "year": int(row['Released_Year']),
                "time": int(row['Runtime']),
                "imdb": float(row['IMDB_Rating']),
                "votes": int(row['No_of_Votes']),
                "meta_score": float(row['Meta_score']) if pd.notna(row['Meta_score']) else None,
                "gross": float(row['Gross']) if float(row['Gross']) > 0 else None,
                "description": str(row['Overview']).strip(),
                "certification_id": certification.id,
            }
            movies_data.append(movie)
        
        return movies_data

    async def _prepare_and_link_associations(
            self,
            data: pd.DataFrame,
            movie_data: List[Dict[str, object]],
            genre_map: Dict[str, object],
            director_map: Dict[str, object],
            star_map: Dict[str, object]
    ) -> tuple[List[Dict[str, int]], List[Dict[str, int]], List[Dict[str, int]]]:
        """
        Prepare many-to-many association data for genres, directors, and stars.

        :return: A tuple of three lists: (movie_genres, movie_directors, movie_stars).
        """
        movie_genres_data: List[Dict[str, int]] = []
        movie_directors_data: List[Dict[str, int]] = []
        movie_stars_data: List[Dict[str, int]] = []

        for idx, (_, row) in enumerate(tqdm(data.iterrows(), total=data.shape[0], desc="Processing associations")):
            if idx >= len(movie_data):
                continue

            for genre_name in str(row['Genre']).split(','):
                genre_name = genre_name.strip()
                if genre_name and genre_name in genre_map:
                    movie_genres_data.append({
                        "movie_index": idx,
                        "genre_id": genre_map[genre_name].id
                    })

            director_name = str(row['Director']).strip()
            if director_name and director_name in director_map:
                movie_directors_data.append({
                    "movie_index": idx,
                    "director_id": director_map[director_name].id
                })

            for star_col in ['Star1', 'Star2', 'Star3', 'Star4']:
                if star_col in row and pd.notna(row[star_col]):
                    star_name = str(row[star_col]).strip()
                    if star_name and star_name in star_map:
                        movie_stars_data.append({
                            "movie_index": idx,
                            "star_id": star_map[star_name].id
                        })

        return movie_genres_data, movie_directors_data, movie_stars_data

    async def seed(self) -> None:
        """
        Main method to seed the database with movie data from the CSV.
        """
        try:
            if self._db_session.in_transaction():
                print("Rolling back existing transaction.")
                await self._db_session.rollback()

            await self._seed_user_groups()

            print("Loading and preprocessing CSV...")
            data = self._preprocess_csv()

            print("Preparing reference data (Genres, Directors, Stars, Certifications)...")
            genre_map, director_map, star_map, certification_map = await self._prepare_reference_data(data)

            print("Preparing movie data...")
            movies_data = await self._prepare_movies_data(data, certification_map)

            print(f"Inserting {len(movies_data)} movies...")
            result = await self._db_session.execute(
                insert(Movie).returning(Movie.id),
                movies_data
            )
            movie_ids = list(result.scalars().all())
            await self._db_session.flush()

            print("Preparing associations...")
            movie_genres_data, movie_directors_data, movie_stars_data = await self._prepare_and_link_associations(
                data, movies_data, genre_map, director_map, star_map
            )

            print("Linking movies with genres...")
            for i, assoc in enumerate(movie_genres_data):
                if assoc["movie_index"] < len(movie_ids):
                    assoc["movie_id"] = movie_ids[assoc["movie_index"]]
                    del assoc["movie_index"]
            
            movie_genres_data = [a for a in movie_genres_data if "movie_id" in a]
            if movie_genres_data:
                await self._db_session.execute(insert(Movie.genres.secondary).values(movie_genres_data))

            print("Linking movies with directors...")
            for i, assoc in enumerate(movie_directors_data):
                if assoc["movie_index"] < len(movie_ids):
                    assoc["movie_id"] = movie_ids[assoc["movie_index"]]
                    del assoc["movie_index"]
            
            movie_directors_data = [a for a in movie_directors_data if "movie_id" in a]
            if movie_directors_data:
                await self._db_session.execute(insert(Movie.directors.secondary).values(movie_directors_data))

            print("Linking movies with stars...")
            for i, assoc in enumerate(movie_stars_data):
                if assoc["movie_index"] < len(movie_ids):
                    assoc["movie_id"] = movie_ids[assoc["movie_index"]]
                    del assoc["movie_index"]
            
            movie_stars_data = [a for a in movie_stars_data if "movie_id" in a]
            if movie_stars_data:
                await self._db_session.execute(insert(Movie.stars.secondary).values(movie_stars_data))

            await self._db_session.commit()
            print(f"Seeding completed successfully! Inserted {len(movie_ids)} movies.")

        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            await self._db_session.rollback()
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            await self._db_session.rollback()
            raise


async def main() -> None:
    """
    The main async entry point for running the database seeder.
    """
    async with get_db() as db_session:
        seeder = CSVDatabaseSeeder(CSV_FILE_PATH, db_session)

        if not await seeder.is_db_populated():
            try:
                await seeder.seed()
                print("Database seeding completed successfully.")
            except Exception as e:
                print(f"Failed to seed the database: {e}")
        else:
            print("Database is already populated. Skipping seeding.")


if __name__ == "__main__":
    asyncio.run(main())
