from datetime import datetime, timedelta

from fastapi import APIRouter

from bot.database import (
    get_stats,
    get_leaderboard,
    get_all_volunteers,
    get_all_events,
    get_achievements,
    get_volunteer_submissions,
    get_recent_submissions,
    get_recent_achievements,
)

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def overall_stats():
    stats = await get_stats()
    completion_rate = 0.0
    if stats["total_events"] > 0:
        completion_rate = round(
            stats["completed_events"] / stats["total_events"] * 100, 1
        )
    return {
        **stats,
        "completion_rate": completion_rate,
    }


@router.get("/leaderboard")
async def leaderboard():
    leaders = await get_leaderboard(10)
    result = []
    for i, v in enumerate(leaders, 1):
        submissions = await get_volunteer_submissions(v["id"])
        result.append({
            "rank": i,
            "id": v["id"],
            "full_name": v["full_name"],
            "city": v["city"],
            "points": v["points"],
            "submission_count": len(submissions),
        })
    return result


@router.get("/achievements")
async def all_achievements():
    volunteers = await get_all_volunteers()
    all_achs = []
    for v in volunteers:
        achs = await get_achievements(v["id"])
        for a in achs:
            all_achs.append({
                **a,
                "volunteer_name": v["full_name"],
            })
    all_achs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return all_achs


@router.get("/activity")
async def activity_feed():
    """Recent activity feed merged from submissions, achievements, and events."""
    try:
        items = []

        # Recent submissions
        submissions = await get_recent_submissions(20)
        for s in submissions:
            vol_name = s.get("volunteer_name") or "Волонтёр"
            ev_title = s.get("event_title") or "мероприятие"
            items.append({
                "type": "submission",
                "description": f"{vol_name} подал(а) отчёт о мероприятии «{ev_title}»",
                "created_at": s.get("created_at", ""),
            })

        # Recent achievements
        achievements = await get_recent_achievements(10)
        for a in achievements:
            vol_name = a.get("volunteer_name") or "Волонтёр"
            title = a.get("title") or "достижение"
            items.append({
                "type": "achievement",
                "description": f"{vol_name} получил(а) достижение «{title}»",
                "created_at": a.get("created_at", ""),
            })

        # Recent events created
        events = await get_all_events()
        for ev in events[:10]:
            title = ev.get("title") or "мероприятие"
            items.append({
                "type": "event",
                "description": f"Создано мероприятие «{title}»",
                "created_at": ev.get("created_at", ""),
            })

        # Sort by created_at DESC, return top 20
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items[:20]
    except Exception:
        return []


@router.get("/stats/charts")
async def chart_data():
    """Chart data for the dashboard: daily events, events by city, status distribution."""
    try:
        events = await get_all_events()

        # Daily events for the last 14 days
        today = datetime.utcnow().date()
        date_counts: dict[str, int] = {}
        for i in range(14):
            d = (today - timedelta(days=13 - i)).isoformat()
            date_counts[d] = 0

        for ev in events:
            sd = ev.get("scheduled_date", "")
            if sd and sd in date_counts:
                date_counts[sd] += 1

        daily_events = [{"date": d, "count": c} for d, c in date_counts.items()]

        # Events by city
        city_counts: dict[str, int] = {}
        for ev in events:
            city = ev.get("location_name") or "Не указано"
            city_counts[city] = city_counts.get(city, 0) + 1
        events_by_city = [{"city": c, "count": n} for c, n in city_counts.items()]

        # Status distribution
        status_dist = {"planned": 0, "completed": 0, "cancelled": 0}
        for ev in events:
            st = ev.get("status", "planned")
            if st in status_dist:
                status_dist[st] += 1

        return {
            "daily_events": daily_events,
            "events_by_city": events_by_city,
            "status_distribution": status_dist,
        }
    except Exception:
        return {
            "daily_events": [],
            "events_by_city": [],
            "status_distribution": {"planned": 0, "completed": 0, "cancelled": 0},
        }
