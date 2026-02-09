#!/bin/bash

# Check if MailHog user and password are set
if [ -n "$MAILHOG_USER" ] && [ -n "$MAILHOG_PASSWORD" ]; then
  # Generate bcrypt-hashed password
  HASHED_PASSWORD=$(MailHog bcrypt "$MAILHOG_PASSWORD")

  # Create authentication file with username and hashed password
  echo "$MAILHOG_USER:$HASHED_PASSWORD" > /mailhog.auth
  echo "Auth file created with user: $MAILHOG_USER and hashed password."

  # Start MailHog with authentication
  exec ~/go/bin/MailHog
else
  echo "MAILHOG_USER or MAILHOG_PASSWORD not set. Starting MailHog without authentication."

  # Start MailHog without authentication (unset MH_AUTH_FILE)
  unset MH_AUTH_FILE
  exec ~/go/bin/MailHog
fi