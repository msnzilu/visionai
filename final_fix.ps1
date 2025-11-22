# Fix script for job_service.py - handles bad database data
$content = Get-Content "g:\Desktop\visionai\backend\app\services\job_service.py" -Raw

# Add the complete fixed _doc_to_job_response method
$pattern = '    def _doc_to_job_response\(self, doc: Dict\[str, Any\]\) -> JobResponse:.*?return JobResponse\(\*\*doc\)'

$replacement = @'
    def _doc_to_job_response(self, doc: Dict[str, Any]) -> JobResponse:
        """Convert MongoDB document to JobResponse with data cleaning"""
        
        doc["id"] = str(doc.pop("_id"))
        
        # Provide defaults for optional fields
        doc.setdefault("employment_type", None)
        doc.setdefault("work_arrangement", None)
        doc.setdefault("experience_level", None)
        doc.setdefault("salary_range", None)
        doc.setdefault("requirements", [])
        doc.setdefault("benefits", [])
        doc.setdefault("skills_required", [])
        doc.setdefault("skills_preferred", [])
        doc.setdefault("external_url", None)
        doc.setdefault("company_info", None)
        doc.setdefault("posted_date", None)
        doc.setdefault("application_deadline", None)
        doc.setdefault("relevance_score", None)
        doc.setdefault("match_score", None)
        doc.setdefault("view_count", 0)
        doc.setdefault("application_count", 0)
        doc.setdefault("is_featured", False)
        doc.setdefault("tags", [])
        
        # Clean invalid data formats (strings instead of objects)
        if isinstance(doc.get("benefits"), list) and doc["benefits"]:
            if doc["benefits"] and isinstance(doc["benefits"][0], str):
                doc["benefits"] = []
        
        if isinstance(doc.get("requirements"), list) and doc["requirements"]:
            if doc["requirements"] and isinstance(doc["requirements"][0], str):
                doc["requirements"] = []
        
        return JobResponse(**doc)
'@

$newContent = $content -replace $pattern, $replacement, [System.Text.RegularExpressions.RegexOptions]::Singleline

Set-Content -Path "g:\Desktop\visionai\backend\app\services\job_service.py" -Value $newContent -NoNewline

Write-Host "Fixed _doc_to_job_response method"
