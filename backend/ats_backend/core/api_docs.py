import markdown
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import os


@require_http_methods(["GET"])
def api_documentation(request):
    """
    Serve API documentation as HTML
    URL: /api/docs/
    """
    
    # Read the markdown file. Try multiple relative locations for robustness.
    candidate_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'API_ENDPOINTS.md'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'API_ENDPOINTS.md'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'API_ENDPOINTS.md')
    ]

    markdown_content = None
    docs_path = None

    for path_candidate in candidate_paths:
        path_candidate = os.path.abspath(path_candidate)
        if os.path.exists(path_candidate):
            docs_path = path_candidate
            break

    if not docs_path:
        # fallback to project root path and current working directory
        for path_candidate in [
            os.path.abspath('API_ENDPOINTS.md'),
            os.path.abspath(os.path.join(os.getcwd(), 'API_ENDPOINTS.md')),
        ]:
            if os.path.exists(path_candidate):
                docs_path = path_candidate
                break

    if not docs_path:
        return JsonResponse({"error": "API documentation not found. Place API_ENDPOINTS.md in project root."}, status=404)

    try:
        with open(docs_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        return JsonResponse({"error": "API documentation not found"}, status=404)
    
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
    
    # Create HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ATS Backend - API Documentation</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                padding: 40px;
                overflow-y: auto;
                max-height: 90vh;
            }}
            
            h1, h2, h3, h4, h5 {{
                margin-top: 30px;
                margin-bottom: 15px;
                color: #667eea;
            }}
            
            h1 {{
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-top: 0;
            }}
            
            h2 {{
                border-left: 4px solid #667eea;
                padding-left: 15px;
                margin-top: 40px;
            }}
            
            h3 {{
                color: #555;
                margin-top: 25px;
            }}
            
            p {{
                margin-bottom: 15px;
            }}
            
            code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                color: #d63384;
            }}
            
            pre {{
                background: #2d2d2d;
                color: #f8f8f2;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                margin: 15px 0;
                border-left: 4px solid #667eea;
            }}
            
            pre code {{
                background: none;
                color: inherit;
                padding: 0;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            
            th {{
                background: #f8f9fa;
                font-weight: 600;
                color: #667eea;
            }}
            
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            
            tr:hover {{
                background: #f0f0f0;
            }}
            
            ul, ol {{
                margin-left: 20px;
                margin-bottom: 15px;
            }}
            
            li {{
                margin-bottom: 8px;
            }}
            
            a {{
                color: #667eea;
                text-decoration: none;
                border-bottom: 1px dotted #667eea;
            }}
            
            a:hover {{
                color: #764ba2;
                border-bottom: 1px solid #764ba2;
            }}
            
            .endpoint {{
                background: #f8f9fa;
                border-left: 4px solid #28a745;
                padding: 15px;
                margin: 15px 0;
                border-radius: 3px;
            }}
            
            .endpoint strong {{
                color: #28a745;
            }}
            
            .base-url {{
                background: #e7f3ff;
                border-left: 4px solid #2196F3;
                padding: 15px;
                margin: 20px 0;
                border-radius: 3px;
                font-weight: bold;
            }}
            
            .toc {{
                background: white;
                border: 1px solid #ddd;
                padding: 20px;
                margin-bottom: 30px;
                border-radius: 5px;
            }}
            
            .toc ul {{
                list-style: none;
                margin: 0;
            }}
            
            .toc li {{
                margin: 5px 0;
            }}
            
            .toc a {{
                color: #667eea;
            }}
            
            .method {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 3px;
                color: white;
                font-weight: bold;
                margin-right: 10px;
                font-size: 12px;
            }}
            
            .method.get {{
                background: #61affe;
            }}
            
            .method.post {{
                background: #49cc90;
            }}
            
            .method.put {{
                background: #fca130;
            }}
            
            .method.delete {{
                background: #f93e3e;
            }}
            
            .method.patch {{
                background: #50e3c2;
            }}
            
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #999;
                font-size: 14px;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 20px;
                }}
                
                table {{
                    font-size: 12px;
                }}
                
                th, td {{
                    padding: 8px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {html_content}
            <div class="footer">
                <p>ATS Backend API Documentation | Last Updated: March 22, 2026</p>
                <p><strong>Base URL:</strong> http://localhost:8000/api</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html_template, content_type='text/html; charset=utf-8')


@require_http_methods(["GET"])
def api_docs_json(request):
    """
    Serve API documentation as JSON for programmatic access
    URL: /api/docs.json
    """

    # Reuse code path lookup from api_documentation
    candidate_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'API_ENDPOINTS.md'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'API_ENDPOINTS.md'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'API_ENDPOINTS.md'),
    ]

    docs_path = None
    for path_candidate in candidate_paths:
        path_candidate = os.path.abspath(path_candidate)
        if os.path.exists(path_candidate):
            docs_path = path_candidate
            break

    if not docs_path:
        for path_candidate in [
            os.path.abspath('API_ENDPOINTS.md'),
            os.path.abspath(os.path.join(os.getcwd(), 'API_ENDPOINTS.md')),
        ]:
            if os.path.exists(path_candidate):
                docs_path = path_candidate
                break

    if not docs_path:
        return JsonResponse({"error": "API documentation not found. Place API_ENDPOINTS.md in project root."}, status=404)

    try:
        with open(docs_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        return JsonResponse({"error": "API documentation not found"}, status=404)

    return JsonResponse({
        "title": "ATS Backend API Documentation",
        "base_url": "http://localhost:8000/api",
        "documentation": markdown_content,
        "generated_at": "2026-03-22"
    })
