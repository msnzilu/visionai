# backend/app/services/analytics_service.py
"""
Analytics Service
Provides application statistics and insights
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for application analytics and reporting"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.applications = db.applications
    
    async def get_application_stats(
        self,
        user_id: str,
        period_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive application statistics"""
        try:
            query = {"user_id": user_id}
            
            if period_days:
                start_date = datetime.utcnow() - timedelta(days=period_days)
                query["created_at"] = {"$gte": start_date}
            
            # Get all applications
            applications = await self.applications.find(query).to_list(length=10000)
            
            # Calculate statistics
            total = len(applications)
            
            # Count by status
            status_counts = defaultdict(int)
            for app in applications:
                status_counts[app.get("status", "unknown")] += 1
            
            # Calculate rates
            submitted = status_counts.get("submitted", 0) + status_counts.get("under_review", 0)
            interviews = status_counts.get("interview_scheduled", 0) + status_counts.get("interviewed", 0)
            offers = status_counts.get("offer_received", 0)
            rejections = status_counts.get("rejected", 0)
            
            interview_rate = (interviews / submitted * 100) if submitted > 0 else 0
            offer_rate = (offers / interviews * 100) if interviews > 0 else 0
            rejection_rate = (rejections / total * 100) if total > 0 else 0
            
            # Get applications by source
            source_counts = defaultdict(int)
            for app in applications:
                source = app.get("application_source", "manual")
                source_counts[source] += 1
            
            # Get applications by company
            company_counts = defaultdict(int)
            for app in applications:
                company = app.get("company", "Unknown")
                company_counts[company] += 1
            
            # Top companies
            top_companies = sorted(
                company_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            stats = {
                "total_applications": total,
                "status_breakdown": dict(status_counts),
                "rates": {
                    "interview_rate": round(interview_rate, 2),
                    "offer_rate": round(offer_rate, 2),
                    "rejection_rate": round(rejection_rate, 2)
                },
                "source_breakdown": dict(source_counts),
                "top_companies": [{"company": c[0], "count": c[1]} for c in top_companies],
                "period_days": period_days,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating application stats: {e}")
            raise
    
    async def get_application_timeline(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get application timeline over specified period"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            applications = await self.applications.find({
                "user_id": user_id,
                "created_at": {"$gte": start_date}
            }).to_list(length=10000)
            
            # Group by date
            daily_counts = defaultdict(int)
            for app in applications:
                date_key = app["created_at"].strftime("%Y-%m-%d")
                daily_counts[date_key] += 1
            
            # Fill in missing dates with 0
            timeline_data = []
            current_date = start_date
            end_date = datetime.utcnow()
            
            while current_date <= end_date:
                date_key = current_date.strftime("%Y-%m-%d")
                timeline_data.append({
                    "date": date_key,
                    "count": daily_counts.get(date_key, 0)
                })
                current_date += timedelta(days=1)
            
            return {
                "timeline": timeline_data,
                "total": len(applications),
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting application timeline: {e}")
            raise
    
    async def get_success_metrics(
        self,
        user_id: str,
        period_days: int = 90
    ) -> Dict[str, Any]:
        """Calculate detailed success metrics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            applications = await self.applications.find({
                "user_id": user_id,
                "created_at": {"$gte": start_date}
            }).to_list(length=10000)
            
            total = len(applications)
            if total == 0:
                return {
                    "total_applications": 0,
                    "conversion_funnel": {},
                    "average_time_to_response": None,
                    "message": "No applications in the specified period"
                }
            
            # Conversion funnel
            submitted = len([a for a in applications if a.get("status") in ["submitted", "under_review"]])
            screened = len([a for a in applications if a.get("status") == "under_review"])
            interviewed = len([a for a in applications if a.get("status") in ["interview_scheduled", "interviewed"]])
            offered = len([a for a in applications if a.get("status") == "offer_received"])
            accepted = len([a for a in applications if a.get("status") == "accepted"])
            rejected = len([a for a in applications if a.get("status") == "rejected"])
            
            # Calculate average response time
            response_times = []
            for app in applications:
                if app.get("status") in ["interview_scheduled", "rejected", "offer_received"]:
                    timeline = app.get("timeline", [])
                    if len(timeline) >= 2:
                        created = app["created_at"]
                        response_event = next(
                            (e for e in timeline if e.get("type") == "status_change"),
                            None
                        )
                        if response_event:
                            response_date = response_event.get("timestamp")
                            if response_date:
                                days = (response_date - created).days
                                response_times.append(days)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else None
            
            return {
                "total_applications": total,
                "conversion_funnel": {
                    "submitted": submitted,
                    "screened": screened,
                    "interviewed": interviewed,
                    "offered": offered,
                    "accepted": accepted,
                    "rejected": rejected
                },
                "conversion_rates": {
                    "to_interview": round((interviewed / submitted * 100) if submitted > 0 else 0, 2),
                    "to_offer": round((offered / interviewed * 100) if interviewed > 0 else 0, 2),
                    "to_acceptance": round((accepted / offered * 100) if offered > 0 else 0, 2)
                },
                "average_response_time_days": round(avg_response_time, 1) if avg_response_time else None,
                "period_days": period_days
            }
            
        except Exception as e:
            logger.error(f"Error calculating success metrics: {e}")
            raise
    
    async def get_source_performance(
        self,
        user_id: str,
        period_days: int = 90
    ) -> List[Dict[str, Any]]:
        """Analyze performance by application source"""
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            applications = await self.applications.find({
                "user_id": user_id,
                "created_at": {"$gte": start_date}
            }).to_list(length=10000)
            
            # Group by source
            source_stats = defaultdict(lambda: {
                "total": 0,
                "interviewed": 0,
                "offered": 0,
                "accepted": 0,
                "rejected": 0
            })
            
            for app in applications:
                source = app.get("application_source", "manual")
                stats = source_stats[source]
                stats["total"] += 1
                
                status = app.get("status")
                if status in ["interview_scheduled", "interviewed"]:
                    stats["interviewed"] += 1
                elif status == "offer_received":
                    stats["offered"] += 1
                elif status == "accepted":
                    stats["accepted"] += 1
                elif status == "rejected":
                    stats["rejected"] += 1
            
            # Calculate rates
            performance = []
            for source, stats in source_stats.items():
                total = stats["total"]
                performance.append({
                    "source": source,
                    "total_applications": total,
                    "interview_rate": round((stats["interviewed"] / total * 100) if total > 0 else 0, 2),
                    "offer_rate": round((stats["offered"] / total * 100) if total > 0 else 0, 2),
                    "acceptance_rate": round((stats["accepted"] / total * 100) if total > 0 else 0, 2),
                    "rejection_rate": round((stats["rejected"] / total * 100) if total > 0 else 0, 2)
                })
            
            # Sort by total applications
            performance.sort(key=lambda x: x["total_applications"], reverse=True)
            
            return performance
            
        except Exception as e:
            logger.error(f"Error analyzing source performance: {e}")
            raise
    
    async def generate_monthly_report(
        self,
        user_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive monthly report"""
        try:
            if not year or not month:
                now = datetime.utcnow()
                year = now.year
                month = now.month
            
            # Calculate date range
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            applications = await self.applications.find({
                "user_id": user_id,
                "created_at": {
                    "$gte": start_date,
                    "$lt": end_date
                }
            }).to_list(length=10000)
            
            # Calculate statistics
            total = len(applications)
            
            status_counts = defaultdict(int)
            for app in applications:
                status_counts[app.get("status", "unknown")] += 1
            
            # Top companies
            company_counts = defaultdict(int)
            for app in applications:
                company_counts[app.get("company", "Unknown")] += 1
            
            top_companies = sorted(
                company_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            report = {
                "period": f"{year}-{month:02d}",
                "total_applications": total,
                "status_breakdown": dict(status_counts),
                "top_companies": [{"company": c[0], "count": c[1]} for c in top_companies],
                "interviews_count": status_counts.get("interview_scheduled", 0) + status_counts.get("interviewed", 0),
                "offers_count": status_counts.get("offer_received", 0),
                "rejections_count": status_counts.get("rejected", 0),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            raise