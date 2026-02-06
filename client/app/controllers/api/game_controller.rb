# app/controllers/api/game_controller.rb
# Handles incoming requests from React, forwards them to
# the Python engine via GameEngineService, returns JSON.

module Api
  class GameController < ApplicationController
    before_action :authenticate_user!   # Devise — must be logged in
    wrap_parameters false
    #protect_from_forgery with: :null_session  # allow JSON POST from React

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
        game_id:     params[:game_id],
        player_id:   current_user.id,
        question_id: params[:question_id],
        answer:      params[:answer]
      )
      render json: result
    end

    # POST /api/game/cast
    def cast
      result = GameEngineService.cast_card(
        game_id:   params[:game_id],
        player_id: current_user.id,
        card_id:   params[:card_id]
      )
      render json: result
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

    def handle_engine_error(e)
      render json: { error: e.message }, status: :service_unavailable
    end
  end
end


