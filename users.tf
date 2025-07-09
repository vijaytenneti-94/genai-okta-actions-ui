resource "okta_user" "example" {
  first_name = "Demo"
  last_name  = "User"
  login      = "demo.user@example.com"
  email      = "demo.user@example.com"
}