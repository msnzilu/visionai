# backend/app/integrations/job_boards/generic_scraper.py
"""
Generic job scraper for public job boards (no API required)
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
import re
from urllib.parse import quote_plus

from app.models.job import JobCreate, JobSource, EmploymentType, WorkArrangement

logger = logging.getLogger(__name__)


class GenericJobScraper:
    """Generic scraper for public job boards"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def search_indeed_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Scrape Indeed job listings (often blocked, use as fallback)"""
        
        jobs = []
        
        try:
            base_url = "https://www.indeed.com/jobs"
            params = f"?q={quote_plus(query)}&l={quote_plus(location)}"
            url = base_url + params
            
            logger.info(f"Scraping Indeed: {url}")
            
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                if not job_cards:
                    job_cards = soup.find_all('td', class_='resultContent')
                
                logger.info(f"Found {len(job_cards)} job cards on Indeed")
                
                for card in job_cards[:limit]:
                    try:
                        job_data = self._extract_indeed_job(card)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        logger.warning(f"Error extracting Indeed job: {e}")
                        continue
                
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Indeed scraping error: {e}")
        
        return jobs
    
    def _extract_indeed_job(self, card) -> Optional[Dict[str, Any]]:
        """Extract job data from Indeed card"""
        
        try:
            title_elem = card.find('h2', class_='jobTitle')
            if not title_elem:
                title_elem = card.find('a', class_='jcs-JobTitle')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            company_elem = card.find('span', class_='companyName')
            company = company_elem.get_text(strip=True) if company_elem else None
            
            location_elem = card.find('div', class_='companyLocation')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            link_elem = card.find('a', class_='jcs-JobTitle')
            if not link_elem:
                link_elem = title_elem.find('a') if title_elem else None
            
            job_url = None
            if link_elem and link_elem.get('href'):
                job_url = f"https://www.indeed.com{link_elem['href']}"
            
            snippet_elem = card.find('div', class_='job-snippet')
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            salary_elem = card.find('div', class_='salary-snippet')
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            date_elem = card.find('span', class_='date')
            posted_date = date_elem.get_text(strip=True) if date_elem else None
            
            if not all([title, company]):
                return None
            
            return {
                'title': title,
                'company': company,
                'location': location or 'Not specified',
                'url': job_url,
                'snippet': snippet,
                'salary': salary,
                'posted_date': posted_date
            }
            
        except Exception as e:
            logger.error(f"Error extracting Indeed job data: {e}")
            return None
    
    async def search_remoteok_jobs(
        self,
        query: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Scrape RemoteOK job listings - FIXED to parse actual HTML structure"""
        
        jobs = []
        
        try:
            url = f"https://remoteok.com/remote-{quote_plus(query)}-jobs"
            
            logger.info(f"Scraping RemoteOK: {url}")
            
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find job rows - they have class="job" and data-id attribute
                job_rows = soup.find_all('tr', class_='job')
                
                logger.info(f"Found {len(job_rows)} job rows on RemoteOK")
                
                for row in job_rows[:limit]:
                    try:
                        job_data = self._extract_remoteok_job(row)
                        if job_data:
                            jobs.append(job_data)
                            logger.debug(f"Extracted: {job_data.get('title')} at {job_data.get('company')}")
                    except Exception as e:
                        logger.warning(f"Error extracting RemoteOK job: {e}")
                        continue
                
                logger.info(f"Successfully extracted {len(jobs)} jobs from RemoteOK")
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"RemoteOK scraping failed: {e}")
        
        return jobs
    
    def _extract_remoteok_job(self, row) -> Optional[Dict[str, Any]]:
        """Extract job data from RemoteOK row - based on actual HTML structure"""
        
        try:
            # Get company/position td
            company_position_td = row.find('td', class_='company_and_position')
            if not company_position_td:
                company_position_td = row.find('td', class_='company')
            
            if not company_position_td:
                return None
            
            # Extract title from h2 with itemprop="title"
            title_elem = company_position_td.find('h2', itemprop='title')
            if not title_elem:
                title_elem = company_position_td.find('h2')
            
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            
            # Extract company from h3 with itemprop="name"
            company_elem = company_position_td.find('h3', itemprop='name')
            if not company_elem:
                company_elem = company_position_td.find('h3')
            
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
            
            # Extract location
            location_elem = company_position_td.find('div', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else 'Remote'
            
            # Extract tags/skills from tags td
            tags = []
            tags_td = row.find('td', class_='tags')
            if tags_td:
                tag_elems = tags_td.find_all(['a', 'div'])
                for tag in tag_elems:
                    tag_text = tag.get_text(strip=True)
                    if tag_text and len(tag_text) < 30:
                        tags.append(tag_text)
            
            # Get job URL from data-href or data-url attribute
            job_url = row.get('data-href') or row.get('data-url')
            if job_url and not job_url.startswith('http'):
                job_url = f"https://remoteok.com{job_url}"
            
            # Extract salary if available
            salary = None
            salary_elem = row.find('div', class_='salary')
            if not salary_elem:
                salary_text = row.get_text()
                salary_match = re.search(r'\$[\d,]+[kK]?', salary_text)
                if salary_match:
                    salary = salary_match.group()
            else:
                salary = salary_elem.get_text(strip=True)
            
            # Build description
            description_parts = []
            if tags:
                description_parts.append(f"Skills: {', '.join(tags[:5])}")
            if salary:
                description_parts.append(f"Salary: {salary}")
            description_parts.append("Remote position")
            
            description = '. '.join(description_parts)
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': job_url or '',
                'snippet': description,
                'salary': salary,
                'tags': tags[:10],
                'posted_date': None
            }
            
        except Exception as e:
            logger.error(f"Error extracting RemoteOK job: {e}", exc_info=True)
            return None
    
    def normalize_job(self, raw_job: Dict[str, Any], source: JobSource) -> JobCreate:
        """Convert scraped job to JobCreate model"""
        
        # Determine work arrangement
        work_arrangement = WorkArrangement.ON_SITE
        location_lower = raw_job.get('location', '').lower()
        snippet_lower = raw_job.get('snippet', '').lower()
        
        if 'remote' in location_lower or source == JobSource.JOB_BOARD:
            work_arrangement = WorkArrangement.REMOTE
        elif 'hybrid' in location_lower or 'hybrid' in snippet_lower:
            work_arrangement = WorkArrangement.HYBRID
        
        # Extract skills
        skills = raw_job.get('tags', [])
        if not skills:
            skills = self._extract_skills_from_text(
                raw_job.get('snippet', '') + ' ' + raw_job.get('title', '')
            )
        
        # Parse posted date
        posted_date = self._parse_relative_date(raw_job.get('posted_date'))
        
        # Get description
        description = raw_job.get('snippet', 'No description available')
        if len(description) < 50:
            description = f"{raw_job.get('title', '')} - {description}"
        
        return JobCreate(
            title=raw_job.get('title', ''),
            description=description,
            company_name=raw_job.get('company', ''),
            location=raw_job.get('location', 'Not specified'),
            source=source,
            external_url=raw_job.get('url'),
            external_id=self._generate_external_id(raw_job),
            work_arrangement=work_arrangement,
            employment_type=EmploymentType.FULL_TIME,
            posted_date=posted_date,
            skills_required=skills[:10]
        )
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract common tech skills from text"""
        
        if not text:
            return []
        
        text_lower = text.lower()
        
        common_skills = [
            "python", "javascript", "java", "c++", "c#", "ruby", "php", "go", "rust",
            "react", "angular", "vue", "node.js", "django", "flask", "spring",
            "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
            "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd",
            "git", "agile", "scrum", "rest api", "graphql", "microservices"
        ]
        
        found_skills = [
            skill for skill in common_skills 
            if skill in text_lower
        ]
        
        return found_skills
    
    def _parse_relative_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse relative date strings"""
        
        if not date_str:
            return datetime.utcnow()
        
        date_str = date_str.lower()
        now = datetime.utcnow()
        
        if any(term in date_str for term in ["just posted", "today"]):
            return now
        elif "yesterday" in date_str:
            return now - timedelta(days=1)
        elif "days ago" in date_str or "day ago" in date_str:
            try:
                days = int(re.search(r'(\d+)', date_str).group(1))
                return now - timedelta(days=days)
            except:
                pass
        
        return now
    
    def _generate_external_id(self, job_data: Dict[str, Any]) -> str:
        """Generate external ID from job data"""
        
        if job_data.get('url'):
            return job_data['url'].split('/')[-1]
        
        import hashlib
        combined = f"{job_data.get('title', '')}{job_data.get('company', '')}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]