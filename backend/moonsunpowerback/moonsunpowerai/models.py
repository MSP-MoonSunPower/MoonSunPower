from django.db import models
from django.utils import timezone

# 개별 질문 항목 모델
class QuestionItem(models.Model):
    # foreign key 수정: 문자열 이름도 변경해야 함
    text = models.ForeignKey('CustomText', on_delete=models.CASCADE, related_name="question_items", null=True, blank=True)
    generated_text = models.ForeignKey('GeneratedText', on_delete=models.CASCADE, related_name="question_items", null=True, blank=True)
    question_text = models.TextField()
    choice1 = models.CharField(max_length=255)
    choice2 = models.CharField(max_length=255)
    choice3 = models.CharField(max_length=255)
    choice4 = models.CharField(max_length=255)
    choice5 = models.CharField(max_length=255)
    answer = models.IntegerField(
        choices=[(1, "Choice 1"), (2, "Choice 2"), (3, "Choice 3"), (4, "Choice 4"), (5, "Choice 5")],
        help_text="Enter the correct choice number (1 to 5)"
    )
    explanation = models.TextField()

    def __str__(self):
        if self.text:
            return f"Question {self.id} for CustomText {self.text.id}"
        elif self.generated_text:
            return f"Question {self.id} for GeneratedText {self.generated_text.id}"
        return f"Question {self.id}"

    def get_correct_answer_text(self):
        return getattr(self, f"choice{self.answer}", "No correct answer set")


# 매일 자동 생성되는 텍스트 모델
class GeneratedText(models.Model):
    subject = models.CharField(max_length=255, null=True, default="")
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Generated Text {self.id} - {self.date.strftime('%Y-%m-%d')}"


# 사용자가 요청한 주제 기반의 텍스트 모델 -> 이름 변경
class CustomText(models.Model):
    subject = models.CharField(max_length=255, null=True, default="")
    difficulty = models.IntegerField(null=True, default=3)
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User Generated Text {self.id} - {self.date.strftime('%Y-%m-%d')}"
