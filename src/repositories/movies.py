from typing import Iterable, Sequence, TypeVar

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.models.movie import Certification, Director, Genre, Movie, Star
from src.enums import OrderStatus
from src.models.order import Order, OrderItem


T = TypeVar("T")


def _movie_load_options() -> tuple:
    return (
        joinedload(Movie.certification),
        selectinload(Movie.genres),
        selectinload(Movie.directors),
        selectinload(Movie.stars),
    )


async def _get_many_by_ids(session: AsyncSession, model: type[T], ids: Sequence[int]) -> list[T]:
    if not ids:
        return []
    result = await session.execute(sa.select(model).where(model.id.in_(ids)))
    return list(result.scalars().all())


def _missing_ids(requested: Sequence[int], found: Iterable) -> list[int]:
    found_ids = {obj.id for obj in found}
    return [i for i in requested if i not in found_ids]


async def get_movie(session: AsyncSession, movie_id: int) -> Movie | None:
    stmt = sa.select(Movie).where(Movie.id == movie_id).options(*_movie_load_options())
    res = await session.execute(stmt)
    return res.scalars().first()


async def list_movies(
    session: AsyncSession,
    *,
    page: int = 1,
    per_page: int = 20,
    q: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    imdb_from: float | None = None,
    imdb_to: float | None = None,
    certification_id: int | None = None,
    sort_by: str = "id",
    sort_dir: str = "desc",
) -> tuple[list[Movie], int]:

    conditions: list = []

    if q:
        like = f"%{q}%"
        conditions.append(sa.or_(Movie.name.ilike(like), Movie.description.ilike(like)))
    if year_from is not None:
        conditions.append(Movie.year >= year_from)
    if year_to is not None:
        conditions.append(Movie.year <= year_to)
    if imdb_from is not None:
        conditions.append(Movie.imdb >= imdb_from)
    if imdb_to is not None:
        conditions.append(Movie.imdb <= imdb_to)
    if certification_id is not None:
        conditions.append(Movie.certification_id == certification_id)

    count_stmt = sa.select(sa.func.count(Movie.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total_items = int((await session.execute(count_stmt)).scalar_one())

    sort_map = {
        "id": Movie.id,
        "year": Movie.year,
        "imdb": Movie.imdb,
        "votes": Movie.votes,
        "price": Movie.price,
        "time": Movie.time,
        "name": Movie.name,
    }
    sort_col = sort_map.get(sort_by, Movie.id)
    order_expr = sa.desc(sort_col) if sort_dir.lower() == "desc" else sa.asc(sort_col)

    stmt = sa.select(Movie).options(*_movie_load_options()).order_by(order_expr)
    if conditions:
        stmt = stmt.where(*conditions)

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    res = await session.execute(stmt)
    items = list(res.scalars().unique().all())
    return items, total_items


async def create_movie(session: AsyncSession, data) -> Movie:

    certification = await session.get(Certification, data.certification_id)
    if not certification:
        raise ValueError("CERTIFICATION_NOT_FOUND")

    genres = await _get_many_by_ids(session, Genre, data.genre_ids)
    directors = await _get_many_by_ids(session, Director, data.director_ids)
    stars = await _get_many_by_ids(session, Star, data.star_ids)

    missing = {
        "genre_ids": _missing_ids(data.genre_ids, genres),
        "director_ids": _missing_ids(data.director_ids, directors),
        "star_ids": _missing_ids(data.star_ids, stars),
    }
    missing = {k: v for k, v in missing.items() if v}
    if missing:
        raise ValueError(f"MISSING_RELATED:{missing}")

    movie = Movie(
        name=data.name,
        year=data.year,
        time=data.time,
        imdb=data.imdb,
        votes=data.votes,
        meta_score=data.meta_score,
        gross=data.gross,
        description=data.description,
        price=data.price,
        certification_id=data.certification_id,
    )
    movie.genres = genres
    movie.directors = directors
    movie.stars = stars

    session.add(movie)

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e

    loaded = await get_movie(session, movie.id)
    return loaded or movie


async def update_movie(session: AsyncSession, movie: Movie, data) -> Movie:
    payload = data.model_dump(exclude_unset=True)

    if "certification_id" in payload:
        cid = payload["certification_id"]
        if cid is not None:
            certification = await session.get(Certification, cid)
            if not certification:
                raise ValueError("CERTIFICATION_NOT_FOUND")
            movie.certification_id = cid

    if "genre_ids" in payload:
        ids = payload["genre_ids"] or []
        genres = await _get_many_by_ids(session, Genre, ids)
        miss = _missing_ids(ids, genres)
        if miss:
            raise ValueError(f"MISSING_RELATED:{{'genre_ids': {miss}}}")
        movie.genres = genres

    if "director_ids" in payload:
        ids = payload["director_ids"] or []
        directors = await _get_many_by_ids(session, Director, ids)
        miss = _missing_ids(ids, directors)
        if miss:
            raise ValueError(f"MISSING_RELATED:{{'director_ids': {miss}}}")
        movie.directors = directors

    if "star_ids" in payload:
        ids = payload["star_ids"] or []
        stars = await _get_many_by_ids(session, Star, ids)
        miss = _missing_ids(ids, stars)
        if miss:
            raise ValueError(f"MISSING_RELATED:{{'star_ids': {miss}}}")
        movie.stars = stars

    scalar_fields = {
        "name",
        "year",
        "time",
        "imdb",
        "votes",
        "meta_score",
        "gross",
        "description",
        "price",
    }
    for key in scalar_fields:
        if key in payload:
            setattr(movie, key, payload[key])

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e

    updated = await get_movie(session, movie.id)
    return updated or movie


async def delete_movie(session: AsyncSession, movie: Movie) -> None:
    stmt = (
        sa.select(
            sa.exists().where(
                sa.and_(
                    OrderItem.movie_id == movie.id,
                    Order.status == OrderStatus.PAID,
                )
            )
        )
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
    )

    is_purchased = bool((await session.execute(stmt)).scalar())
    if is_purchased:
        raise ValueError("MOVIE_PURCHASED")

    await session.delete(movie)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e


async def list_genres(session: AsyncSession) -> list[Genre]:
    res = await session.execute(sa.select(Genre).order_by(Genre.name))
    return list(res.scalars().all())


async def get_genre(session: AsyncSession, genre_id: int) -> Genre | None:
    return await session.get(Genre, genre_id)


async def create_genre(session: AsyncSession, name: str) -> Genre:
    genre = Genre(name=name)
    session.add(genre)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
    await session.refresh(genre)
    return genre


async def update_genre(session: AsyncSession, genre: Genre, name: str) -> Genre:
    genre.name = name
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
    await session.refresh(genre)
    return genre


async def delete_genre(session: AsyncSession, genre: Genre) -> None:
    await session.delete(genre)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e


async def list_stars(session: AsyncSession) -> list[Star]:
    res = await session.execute(sa.select(Star).order_by(Star.name))
    return list(res.scalars().all())


async def get_star(session: AsyncSession, star_id: int) -> Star | None:
    return await session.get(Star, star_id)


async def create_star(session: AsyncSession, name: str) -> Star:
    star = Star(name=name)
    session.add(star)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
    await session.refresh(star)
    return star


async def update_star(session: AsyncSession, star: Star, name: str) -> Star:
    star.name = name
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
    await session.refresh(star)
    return star


async def delete_star(session: AsyncSession, star: Star) -> None:
    await session.delete(star)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e


async def list_directors(session: AsyncSession) -> list[Director]:
    res = await session.execute(sa.select(Director).order_by(Director.name))
    return list(res.scalars().all())


async def get_director(session: AsyncSession, director_id: int) -> Director | None:
    return await session.get(Director, director_id)


async def create_director(session: AsyncSession, name: str) -> Director:
    director = Director(name=name)
    session.add(director)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
    await session.refresh(director)
    return director


async def update_director(session: AsyncSession, director: Director, name: str) -> Director:
    director.name = name
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
    await session.refresh(director)
    return director


async def delete_director(session: AsyncSession, director: Director) -> None:
    await session.delete(director)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e


async def list_certifications(session: AsyncSession) -> list[Certification]:
    res = await session.execute(sa.select(Certification).order_by(Certification.name))
    return list(res.scalars().all())


async def get_certification(session: AsyncSession, certification_id: int) -> Certification | None:
    return await session.get(Certification, certification_id)


async def create_certification(session: AsyncSession, name: str) -> Certification:
    cert = Certification(name=name)
    session.add(cert)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
    await session.refresh(cert)
    return cert


async def update_certification(session: AsyncSession, cert: Certification, name: str) -> Certification:
    cert.name = name
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
    await session.refresh(cert)
    return cert


async def delete_certification(session: AsyncSession, cert: Certification) -> None:
    await session.delete(cert)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise e
