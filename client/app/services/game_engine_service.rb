# app/services/game_engine_service.rb
# This class handles ALL communication with the Python game engine.
# It's the only place in Rails that "knows" about the Python server.

class GameEngineService
  require 'net/http'
  require 'uri'
  require 'json'

  # URL where your Python game engine is running
  ENGINE_URL = ENV.fetch('GAME_ENGINE_URL', 'http://localhost:8000')

  # ── Start a new game ──
  def self.start_game(player_id:, mode:, opponent_id: nil)
    post('/game/start', {
      player_id:   player_id,
      mode:        mode,
      opponent_id: opponent_id
    })
  end

  # ── Submit a flashcard answer ──
  def self.answer_question(game_id:, player_id:, question_id:, answer:)
    post('/game/answer', {
      game_id:     game_id,
      player_id:   player_id,
      question_id: question_id,
      answer:      answer
    })
  end

  # ── Cast a card ──
  def self.cast_card(game_id:, player_id:, hand_index:)
  post('/game/play', {
    game_id:    game_id,
    player_id:  player_id,
    hand_index: hand_index
  })
end

  # ── Get current game state ──
  def self.game_state(game_id:)
    get("/game/state/#{game_id}")
  end

  # ── End the current turn ──
  def self.end_turn(game_id:)
    post('/game/endturn', {
      game_id: game_id
    })
  end

  # ── End / forfeit a game ──
  def self.end_game(game_id:, player_id:, reason:)
    post('/game/end', {
      game_id:   game_id,
      player_id: player_id,
      reason:    reason
    })
  end

  # ─────────────────────────────────
  #  Private helpers — HTTP plumbing
  # ─────────────────────────────────

  private_class_method def self.post(path, body)
    uri  = URI("#{ENGINE_URL}#{path}")
    http = Net::HTTP.new(uri.host, uri.port)

    request = Net::HTTP::Post.new(uri.path, 'Content-Type' => 'application/json')
    request.body = body.to_json

    response = http.request(request)
    parse_response(response)
  end

  private_class_method def self.get(path)
    uri      = URI("#{ENGINE_URL}#{path}")
    response = Net::HTTP.get_response(uri)
    parse_response(response)
  end

  private_class_method def self.parse_response(response)
    data = JSON.parse(response.body)

    unless response.is_a?(Net::HTTPOK)
      raise GameEngineError, data["error"] || "Game engine returned #{response.code}"
    end

    data
  rescue JSON::ParserError
    raise GameEngineError, "Invalid response from game engine"
  end
end

# Custom error class so Rails can handle game engine failures gracefully

