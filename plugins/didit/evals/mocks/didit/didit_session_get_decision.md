{
  "session_id": "3c2b1a00-0000-4000-8000-0000000000aa",
  "status": "Declined",
  "id_verifications": [
    {
      "node_id": "feature_ocr",
      "status": "Declined",
      "document_type": "Passport",
      "issuing_state": "ESP",
      "warnings": [
        {
          "risk": "LOW_QUALITY_IMAGE",
          "short_description": "Document image too blurry to read"
        }
      ]
    }
  ],
  "liveness_checks": [
    {
      "node_id": "feature_liveness",
      "status": "Approved",
      "score": 96.4
    }
  ],
  "face_matches": [
    {
      "node_id": "feature_face",
      "status": "Approved",
      "score": 88.1
    }
  ],
  "aml_screenings": [
    {
      "node_id": "feature_aml",
      "status": "Approved",
      "total_hits": 0
    }
  ]
}
