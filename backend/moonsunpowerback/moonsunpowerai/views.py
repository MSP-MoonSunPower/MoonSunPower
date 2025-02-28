import os
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from openai import OpenAI
from .models import CustomText, GeneratedText, QuestionItem
from .prompts import *
from dotenv import load_dotenv
import re

load_dotenv()

class TodayTextAPIView(APIView):
    """
    API to fetch the latest generated text entry along with its related question items.
    """

    @swagger_auto_schema(
        operation_summary="Get the latest generated text with related questions",
        operation_description="Fetches the most recent generated text along with associated question items.",
        responses={
            200: openapi.Response(
                description="Successful response",
                examples={
                    "application/json": {
                        "content": "Generated content here...",
                        "date": "2023-01-01",
                        "questions": [
                            {
                                "question_text": "Sample question?",
                                "choice1": "Option 1",
                                "choice2": "Option 2",
                                "choice3": "Option 3",
                                "choice4": "Option 4",
                                "choice5": "Option 5",
                                "answer": 1,
                                "explanation": "Sample explanation"
                            }
                        ]
                    }
                }
            ),
            404: openapi.Response(
                description="No content found",
                examples={
                    "application/json": {
                        "error": "No content found"
                    }
                }
            ),
        }
    )
    def get(self, request):
        # 가장 최근의 GeneratedText 가져오기
        latest_text = GeneratedText.objects.order_by('-date').first()
        
        if latest_text:
            # 관련된 QuestionItems 가져오기
            data=json.loads(latest_text.content)
            questions = latest_text.question_items.all()
            questions_data = [
                {
                    "question_text": question.question_text,
                    "choice1": question.choice1,
                    "choice2": question.choice2,
                    "choice3": question.choice3,
                    "choice4": question.choice4,
                    "choice5": question.choice5,
                    "answer": question.answer,
                    "explanation": question.explanation
                }
                for question in questions
            ]
            
            response_data = {
                "content": data["content"],
                "date": latest_text.date,
                "questions": questions_data
            }
            return Response(response_data, status=status.HTTP_200_OK)
        
        # GeneratedText가 없을 경우
        return Response({'error': 'No content found'}, status=status.HTTP_404_NOT_FOUND)

class GenerateTextAPIView(APIView):
    """
    주어진 subject와 difficulty에 따라 교육용 텍스트를 생성하는 API 뷰입니다.
    """
    
    def get(self, request, subject, difficulty, *args, **kwargs):
        if not subject:
            return Response(
                {"error": "Subject parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # USER_SELECT_TEXT_PROMPTS에서 해당 난이도의 프롬프트를 가져옵니다.
        prompt_key = f"user_select_text_prompt_{difficulty}"
        if prompt_key not in USER_SELECT_TEXT_PROMPTS:
            print(prompt_key)
            return Response(
                {"error": "Invalid difficulty level. Choose a value between 1 and 4."},
                status=status.HTTP_400_BAD_REQUEST
            )
        prompt_text = USER_SELECT_TEXT_PROMPTS[prompt_key]
        
        try:
            text_length = int(TEXT_LENGTH[str(difficulty)])
        except (KeyError, ValueError):
            return Response(
                {"error": "Invalid text length configuration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model = str(MODEL_SELECTOR.get(f"model_type_{difficulty}")).strip(),
            messages=[
                {
                    "role": "system",
                    "content": prompt_text
                },
                {
                    "role": "user",
                    "content": subject
                },
            ],
            response_format={
            "type": "json_object"
                },
            temperature=1,
            max_tokens=text_length,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        print(response)
        content_raw = response.choices[0].message.content
        print(content_raw)
        if not content_raw or "error" in content_raw:
            return Response(
                {"error": "No content received from OpenAI API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            content_data = json.loads(content_raw)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON format in API response"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        main_content = content_data.get("content", "")
        questions = content_data.get("questions", [])

        generated_text = CustomText.objects.create(
            subject=subject,
            difficulty=difficulty,
            content=main_content
        )

        questions_data = []
        for question in questions:
            question_item = QuestionItem.objects.create(
                text=generated_text,
                question_text=question["question_text"],
                choice1=question["choice1"],
                choice2=question["choice2"],
                choice3=question["choice3"],
                choice4=question["choice4"],
                choice5=question["choice5"],
                answer=int(question["answer"]),
                explanation=question["explanation"]
            )
            questions_data.append({
                "question_text": question_item.question_text,
                "choice1": question_item.choice1,
                "choice2": question_item.choice2,
                "choice3": question_item.choice3,
                "choice4": question_item.choice4,
                "choice5": question_item.choice5,
                "answer": question_item.answer,
                "explanation": question_item.explanation
            })

        response_data = {
            "subject": generated_text.subject,
            "content": generated_text.content,
            "date": generated_text.date,
            "questions": questions_data
        }

        return Response(response_data, status=status.HTTP_200_OK)

class GenerateTagTextAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Generate educational text and questions based on subject and difficulty level.",
        manual_parameters=[
            openapi.Parameter(
                'subject',
                openapi.IN_PATH,
                description="Subject code (integer between 1 and 6) for generating educational text",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'difficulty',
                openapi.IN_PATH,
                description="Difficulty level (integer between 1 and 4) for educational content",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Response(
                description="Successfully generated educational content and questions",
                examples={
                    "application/json": {
                        "subject": 1,
                        "content": "Generated educational content about the subject",
                        "date": "2023-01-01T00:00:00Z",
                        "questions": [
                            {
                                "question_text": "What is 2+2?",
                                "choice1": "3",
                                "choice2": "4",
                                "choice3": "5",
                                "choice4": "6",
                                "choice5": "7",
                                "answer": 2,
                                "explanation": "The correct answer is 4."
                            }
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid parameters or API request errors",
                examples={
                    "application/json": {
                        "error": "Invalid difficulty level. Choose a value between 1 and 4."
                    }
                }
            ),
            500: openapi.Response(
                description="Server error or unexpected response from OpenAI API",
                examples={
                    "application/json": {
                        "error": "No content received from OpenAI API"
                    }
                }
            )
        }
    )
    
    def get(self, request, subject, difficulty, *args, **kwargs):
        # subject를 문자열로 전달하여 setPresetPrompt에서 제대로 찾을 수 있도록 함
        prompt_text = setPresetPrompt(subject, difficulty)
        print(prompt_text)
        if not prompt_text:
            return Response(
                {"error": "태그 주제 텍스트를 찾을 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        try:
            text_length = int(TEXT_LENGTH[str(difficulty)])
        except (KeyError, ValueError):
            return Response(
                {"error": "Invalid text length configuration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt_text
                },
                {
                    "role": "user",
                    "content": "지문 생성"
                },
            ],
            temperature=1,
            max_tokens=text_length,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={
                "type": "json_object"      
            }
        )
        
        content_raw = response.choices[0].message.content
        if not content_raw:
            return Response({"error": "No content received from OpenAI API"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if "error" in content_raw:
            return Response({"error": "죄송합니다. 다른 단어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            content_data = json.loads(content_raw)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format in API response"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        main_content = content_data.get("content", "")
        questions = content_data.get("questions", [])

        generated_text = CustomText.objects.create(
            subject=subject,
            difficulty=difficulty,
            content=main_content
        )

        questions_data = []
        for question in questions:
            question_item = QuestionItem.objects.create(
                text=generated_text,
                question_text=question["question_text"],
                choice1=question["choice1"],
                choice2=question["choice2"],
                choice3=question["choice3"],
                choice4=question["choice4"],
                choice5=question["choice5"],
                answer=int(question["answer"]),
                explanation=question["explanation"]
            )
            questions_data.append({
                "question_text": question_item.question_text,
                "choice1": question_item.choice1,
                "choice2": question_item.choice2,
                "choice3": question_item.choice3,
                "choice4": question_item.choice4,
                "choice5": question_item.choice5,
                "answer": question_item.answer,
                "explanation": question_item.explanation
            })

        response_data = {
            "subject": generated_text.subject,
            "content": generated_text.content,
            "date": generated_text.date,
            "questions": questions_data
        }

        return Response(response_data, status=status.HTTP_200_OK)
class UnknownWordsAPIView(APIView):
    @swagger_auto_schema(
        operation_description="사전 API: 입력된 단어 또는 구에 대해 각각의 기본형과 정의를 반환합니다. 단일 단어 입력 시 단일 JSON 객체, 여러 단어 입력 시 JSON 배열로 출력합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'unknown_words': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="정의할 단어 혹은 구의 목록"
                ),
                'difficulty': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="난이도 (1-4)"
                ),
            },
            required=['unknown_words', 'difficulty'],
        ),
        responses={200: "Success", 400: "Invalid input"}
    )
    def post(self, request, *args, **kwargs):
        unknown_words = request.data.get("unknown_words", [])
        difficulty = request.data.get("difficulty")
        if not unknown_words:
            return Response({"error": "No words provided"}, status=status.HTTP_400_BAD_REQUEST)
        if difficulty not in range(1, 5):
            return Response(
                {"error": "Invalid difficulty level. Choose a value between 1 and 4."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # WORD_DEFINITION_DICTIONARY에서 난이도에 맞는 프롬프트를 가져옵니다.
        prompt_key = f"word_definition_dictionary_{difficulty}"
        if prompt_key not in WORD_DEFINITION_DICTIONARY:
            return Response(
                {"error": "No definition prompt available for this difficulty."},
                status=status.HTTP_400_BAD_REQUEST
            )
        prompt_text = WORD_DEFINITION_DICTIONARY[prompt_key]
        
        # 사전 역할 수행을 위한 상세 지시사항을 추가합니다.
        instructions = (
            "너는 사전이다. 사용자가 입력한 단어 또는 구에 대해 각 기본형과 정의를 "
            "JSON 형식으로 반환하라. \n"
            "출력 형식:\n"
            "- 단일 단어 입력 시: {\"word\": \"<기본형>\", \"definition\": \"<의미>\"}\n"
            "- 여러 단어 입력 시: [{\"word\": \"<기본형>\", \"definition\": \"<의미>\"}, ...]\n"
            "문장 부호는 제거하고, 동사와 형용사의 활용형은 반드시 기본형으로 변환하라. "
            "정의는 정확하고 전문적으로 제공하라. 단어를 인식할 수 없으면 'error'라고 표시하라."
        )
        
        # instructions, 프롬프트 텍스트, 그리고 입력 단어들을 하나의 입력으로 구성합니다.
        prompt_input = f"{instructions}\n{prompt_text}\nWords: {', '.join(unknown_words)}"
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt_text
                },
                {
                    "role": "user",
                    "content": prompt_input
                },
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        try:
            response_data = json.loads(content)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON format in API response"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 입력 단어가 여러 개인 경우에는 JSON 배열, 단일 단어면 단일 객체 반환
        if len(unknown_words) > 1:
            if not isinstance(response_data, list):
                response_data = [response_data]
        else:
            if isinstance(response_data, list) and len(response_data) > 0:
                response_data = response_data[0]
        print(response_data)
        return Response(response_data, status=status.HTTP_200_OK)