# app/controllers/api/game_controller.rb
# Handles incoming requests from React, forwards them to
# the Python engine via GameEngineService, returns JSON.

class GamesController < ApplicationController
    before_action :authenticate_user!   # Devise — must be logged in
    wrap_parameters false
    #protect_from_forgery with: :null_session  # allow JSON POST from React

  def create
    # 1. Call the Python Engine
    # Note: We rely on the Python engine to return a JSON with { "game_id": "..." }
    response = GameEngineService.start_game(
      player_id:   current_user.id,
      mode:        params[:mode],
      opponent_id: params[:opponent_id].presence # Sends nil if empty string
    )

    # 2. Redirect to the Game Board (show action)
    # The 'response' hash must contain the key 'game_id'
    redirect_to game_path(response['game_id'])

  rescue GameEngineError => e
    # 3. Handle failures (e.g., Python server is down)
    flash[:alert] = "Failed to start game: #{e.message}"
    redirect_to root_path
  end

  def show
    # IF we are in development and passed ?mock=true in the URL...
    if params[:mock] == "true"
      @game_state = mock_state
    else
      # Otherwise, try to talk to Python
      @game_state = GameEngineService.game_state(game_id: params[:id])
    end
    rescue GameEngineError => e
      flash[:alert] = "Game not found or finished."
      redirect_to root_path
  end

    # POST /api/game/start
    def start
      result = GameEngineService.start_game(
        player_id:   current_user.id,
        mode:        params[:mode],
        opponent_id: params[:opponent_id]
      )
      render json: result
    end

    # POST /api/game/answer
    def answer
      result = GameEngineService.answer_question(
        game_id:     params[:id],
        player_id:   current_user.id,
        question_id: nil,
        answer:      params[:answer]
      )

      render turbo_stream: turbo_stream.update(
        "game_board", 
        partial: "games/board", 
        locals: { state: result }
      )
    rescue GameEngineError => e
      render turbo_stream: turbo_stream.update("flash", html: e.message)
end

    # POST /api/game/cast
    def cast
      new_state = GameEngineService.cast_card(
        game_id:   params[:id],
        player_id: current_user.id,
hand_index: params[:hand_index].to_i
      )

      respond_to do |format|
        format.turbo_stream do
          render turbo_stream: turbo_stream.update(
            "game_board", 
            partial: "games/board", 
            locals: { state: new_state }
          )
        end
      end
    end

    # GET /api/game/state?game_id=abc-123
    def state
      result = GameEngineService.game_state(game_id: params[:game_id])
      render json: result
    end

    # POST /api/game/end
    def end_game
      result = GameEngineService.end_game(
        game_id:   params[:game_id],
        player_id: current_user.id,
        reason:    params[:reason]
      )
      render json: result
    end

    # ── If anything goes wrong, return a clean JSON error ──
    rescue_from GameEngineError, with: :handle_engine_error

    private

    # app/controllers/games_controller.rb

private

def mock_state
  {
    "game_id": "ef8fd681-7491-4ece-a672-becdde182cf3",
    "phase": "questions",
    "turn": 1,
    "player_hp": 60,
    "player_max_hp": 60,
    "player_mana": 0,
    "boss_hp": 90,
    "boss_max_hp": 90,
    "boss_resists": "water",
    "hand": [
        "Ice Attack (12)",
        "Water Attack (12)",
        "Block Fire",
        "Block Ice",
        "Fire Attack (12)"
    ],
    "questions_left": 2,
    "current_question": "What does CPU stand for?",
    "game_over": false,
    "winner": null,
    "log": [
        "Turn 1 begins. Boss resists water.",
        "Drew up to 5 cards.",
        "Wrong. +0 mana."
    ],
    "answer_correct": false
}
end

    def handle_engine_error(e)
      render json: { error: e.message }, status: :service_unavailable
    end
  end


