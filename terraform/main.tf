terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "YOUR_GCP_PROJECT_ID"
  region  = "us-central1"
}

resource "google_cloud_run_service" "bark_tts" {
  name     = "bark-tts-api"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/YOUR_GCP_PROJECT_ID/bark-tts-api"
        ports {
          container_port = 5000
        }
        env {
          name  = "PORT"
          value = "5000"
        }
      }
    }
  }

  metadata {
    annotations = {
      "run.googleapis.com/launch-stage" = "BETA"
    }
  }
}

resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.bark_tts.name
  location = google_cloud_run_service.bark_tts.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
