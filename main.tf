terraform {
  cloud {
    organization = "LVLPEDIA"  # Change this to your Terraform Cloud org
    workspaces {
      name = "LVLPEDIA_TTS_BARK" # Change this if needed
    }
  }
}

provider "google" {
  project = "lvlpedia-tts-bark" # Change this to your GCP project ID
  region  = "us-central1"
}

resource "google_cloud_run_service" "bark_tts" {
  name     = "bark-tts-api"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/lvlpedia-tts-bark/bark-tts-api"
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
