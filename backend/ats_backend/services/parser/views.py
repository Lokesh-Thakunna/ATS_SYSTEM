from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .resume_parser import parse_resume

@api_view(['POST'])
def parse_resume_view(request):
    """
    Parse uploaded resume file and extract skills, experience, and projects
    """
    file = request.FILES.get("resume")

    if not file:
        return Response(
            {"error": "No file uploaded"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate file type
    allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    if file.content_type not in allowed_types:
        return Response(
            {"error": "Invalid file type. Only PDF, DOCX, and TXT files are supported"},
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    try:
        # Read file bytes
        file_bytes = file.read()

        # Parse resume
        parsed_data = parse_resume(file_bytes, file.content_type)

        return Response({
            "message": "Resume parsed successfully",
            "data": parsed_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"Error parsing resume: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
