# Script to fix job_service.py with proper defaults handling
$filePath = "g:\Desktop\visionai\backend\app\services\job_service.py"
$content = Get-Content $filePath -Raw

# Find and replace the _doc_to_job_response method
$oldMethod = @'
    def _doc_to_job_response(self, doc: Dict[str, Any]) -> JobResponse:
        """Convert MongoDB document to JobResponse"""
        
        doc["id"] = str(doc.pop("_id"))
        return JobResponse(**doc)
'@

$newMethod = @'
    def _doc_to_job_response(self, doc: Dict[str, Any]) -> JobResponse:
        """Convert MongoDB document to JobResponse"""
        
        doc["id"] = str(doc.pop("_id"))
        
        # Provide defaults for optional fields that might be missing
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
        
        return JobResponse(**doc)
'@

$newContent = $content -replace [regex]::Escape($oldMethod), $newMethod

Set-Content -Path $filePath -Value $newContent -NoNewline

Write-Host "Successfully updated _doc_to_job_response method"
