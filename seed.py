from app import app, db, PDFContent, create_tables

def seed_data():
    # Push application context to avoid 'Working outside of application context' error
    with app.app_context():
        # Create tables if they do not exist
        create_tables()

        # Insert sample PDF text into the PDFContent table (You can change the content accordingly)
        sample_pdf_texts = [
            "This is a sample PDF text content for testing.",
            "Here is another example of PDF text content."
        ]

        for text in sample_pdf_texts:
            pdf_content = PDFContent(text=text)
            db.session.add(pdf_content)

        # Commit the changes to the database
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_data()