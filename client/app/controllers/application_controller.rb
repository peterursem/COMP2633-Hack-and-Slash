class ApplicationController < ActionController::Base
  # Only allow modern browsers supporting webp images, web push, badges, import maps, CSS nesting, and CSS :has.
  allow_browser versions: :modern

  # Changes to the importmap will invalidate the etag for HTML responses
  stale_when_importmap_changes

  # Ensures CSRF protection for forms and requests
  protect_from_forgery with: :exception

   # Skip CSRF for JSON API requests only (these are protected by authenticate_user! instead)
  skip_before_action :verify_authenticity_token, if: :json_request?

  before_action :configure_permitted_parameters, if: :devise_controller?

  protected

  def configure_permitted_parameters
    devise_parameter_sanitizer.permit(
      :sign_up,
      keys: [:username]
    )

    devise_parameter_sanitizer.permit(
      :account_update,
      keys: [:username]
    )
  end

  def after_sign_in_path_for(resource)
    dashboard_path
  end

  def after_sign_out_path_for(_resource_or_scope)
    root_path
  end

  private

  # Returns true if the request Content-Type is JSON
  def json_request?
    request.content_type&.include?('application/json')
  end

end
