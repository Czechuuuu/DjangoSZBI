from .models import Document, DocumentLog

class Workflow:
    @staticmethod
    def send_to_review(document, user):
        document.status = 'review'
        document.save()
        DocumentLog.objects.create(
            document=document,
            user=user,
            action="send_to_review",
            description="Dokument przesłany do recenzji."
        )

    @staticmethod
    def approve(document, user):
        document.status = 'approval'
        document.save()
        DocumentLog.objects.create(
            document=document,
            user=user,
            action="approved",
            description="Dokument zatwierdzony."
        )

    @staticmethod
    def publish(document, user):
        document.status = 'published'
        document.save()
        DocumentLog.objects.create(
            document=document,
            user=user,
            action="published",
            description="Dokument opublikowany."
        )
