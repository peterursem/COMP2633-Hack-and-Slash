> [!IMPORTANT]
> The branches were combined after the deadline of the hackathon. All code is unaffected and is in seperate folders regardless. A true timeline of our work is avaliable in the branches "frontend" and "bryanFork"

# Hack And Flash
A game made for our first COMP2633 hackathon.

## Install

## Server

Ensure you have **Python 3** installed and updated
Install **FastAPI** and **Uvicorn** using `pip`

## Client

Install **Rails 8** and **Postgres**
Start a postgres server locally
From the client directory, run:
`bundle install
rails db:create
rails db:migrate
rails s`

## Running the game

### Server
From the server directory, run
`uvicorn engine:app --host 127.0.0.1 --port 8000`

### Client
From the client directory, run
`rails s`
