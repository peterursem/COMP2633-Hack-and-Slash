# app/lib/game_engine_error.rb
# Custom error class for game engine failures.
# Lives in its own file so Rails can autoload it from anywhere.

class GameEngineError < StandardError; end
