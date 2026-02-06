class DashboardController < ApplicationController
  # Require user is logged in before doing anything
  before_action :authenticate_user!

  def index
  end
end
