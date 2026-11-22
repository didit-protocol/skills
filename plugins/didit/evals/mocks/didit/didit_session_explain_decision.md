{
  "session_id": "3c2b1a00-0000-4000-8000-0000000000aa",
  "status": "Declined",
  "reasons": [
    {
      "node": "ID verification",
      "code": "LOW_QUALITY_IMAGE",
      "explanation": "The passport photo was too blurry for the text to be read. Liveness, face match and AML passed."
    }
  ],
  "levers": [
    {
      "action": "resubmit",
      "nodes": [
        "feature_ocr"
      ],
      "explanation": "Ask the person to retake the document photo."
    }
  ]
}
