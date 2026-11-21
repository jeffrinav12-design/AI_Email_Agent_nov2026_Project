from gmail_service import create_draft


draft_id = create_draft(
    "jeffrinavcsda2024@sankara.ac.in",
    "Email Agent Test",
    "Hello, this is a test draft created by my Python Email Agent."
)

print("Draft created successfully!")
print("Draft ID:", draft_id)