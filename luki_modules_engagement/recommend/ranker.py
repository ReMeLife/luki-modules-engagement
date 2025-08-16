"""
Hybrid scoring and re-ranking system for recommendations.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import math

import numpy as np
from sqlalchemy.orm import Session

from ..config import EngagementConfig
from ..database import get_db_session
from ..models import UserInteraction, EngagementMetric, FeedbackItem

logger = logging.getLogger(__name__)


class RecommendationRanker:
    """
    Provides hybrid scoring and re-ranking for recommendations.
    Combines multiple signals to optimize recommendation quality.
    """
    
    def __init__(self, config: Optional[EngagementConfig] = None):
        self.config = config or EngagementConfig()
        
        # Ranking weights
        self.weights = {
            'interest_similarity': 0.4,
            'engagement_score': 0.25,
            'recency': 0.15,
            'diversity': 0.1,
            'feedback_quality': 0.1
        }
    
    def rank_user_recommendations(self, user_id: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank user recommendation candidates using hybrid scoring.
        
        Args:
            user_id: Target user ID
            candidates: List of candidate recommendation dictionaries
            
        Returns:
            Ranked list of recommendations with scores
        """
        logger.info(f"Ranking {len(candidates)} user recommendations for {user_id}")
        
        if not candidates:
            return []
        
        # Get user context for ranking
        user_context = self._get_user_context(user_id)
        
        # Calculate scores for each candidate
        scored_candidates = []
        for candidate in candidates:
            scores = self._calculate_candidate_scores(user_id, candidate, user_context)
            
            # Calculate weighted final score
            final_score = sum(
                scores.get(factor, 0.0) * weight
                for factor, weight in self.weights.items()
            )
            
            candidate_with_score = {
                **candidate,
                'final_score': final_score,
                'score_breakdown': scores
            }
            scored_candidates.append(candidate_with_score)
        
        # Apply diversity penalty to avoid too similar recommendations
        scored_candidates = self._apply_diversity_penalty(scored_candidates)
        
        # Sort by final score
        scored_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"Ranked recommendations with scores: {[c['final_score']:.3f for c in scored_candidates[:5]]}")
        return scored_candidates
    
    def rank_event_recommendations(self, user_id: str, events: List[Tuple[Dict[str, Any], float]]) -> List[Dict[str, Any]]:
        """
        Rank event recommendations with additional temporal and capacity factors.
        
        Args:
            user_id: Target user ID
            events: List of (event, match_score) tuples
            
        Returns:
            Ranked list of event recommendations
        """
        logger.info(f"Ranking {len(events)} event recommendations for {user_id}")
        
        if not events:
            return []
        
        user_context = self._get_user_context(user_id)
        
        scored_events = []
        for event, base_match_score in events:
            # Calculate additional scoring factors
            temporal_score = self._calculate_temporal_score(event, user_context)
            capacity_score = self._calculate_capacity_score(event)
            popularity_score = self._calculate_popularity_score(event)
            
            # Combine scores
            final_score = (
                base_match_score * 0.5 +
                temporal_score * 0.2 +
                capacity_score * 0.15 +
                popularity_score * 0.15
            )
            
            event_recommendation = {
                **event,
                'final_score': final_score,
                'base_match_score': base_match_score,
                'temporal_score': temporal_score,
                'capacity_score': capacity_score,
                'popularity_score': popularity_score
            }
            scored_events.append(event_recommendation)
        
        # Sort by final score
        scored_events.sort(key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"Ranked event recommendations with scores: {[e['final_score']:.3f for e in scored_events[:5]]}")
        return scored_events
    
    def personalize_ranking(self, user_id: str, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply personalization based on user's historical preferences and feedback.
        
        Args:
            user_id: Target user ID
            recommendations: List of recommendations to personalize
            
        Returns:
            Personalized ranking of recommendations
        """
        logger.info(f"Personalizing ranking for user {user_id}")
        
        # Get user's historical feedback patterns
        feedback_patterns = self._analyze_user_feedback_patterns(user_id)
        
        # Adjust scores based on patterns
        personalized_recommendations = []
        for rec in recommendations:
            adjustment_factor = self._calculate_personalization_adjustment(rec, feedback_patterns)
            
            personalized_rec = {
                **rec,
                'personalized_score': rec.get('final_score', 0.0) * adjustment_factor,
                'personalization_factor': adjustment_factor
            }
            personalized_recommendations.append(personalized_rec)
        
        # Re-sort by personalized score
        personalized_recommendations.sort(key=lambda x: x['personalized_score'], reverse=True)
        
        logger.info(f"Applied personalization to {len(personalized_recommendations)} recommendations")
        return personalized_recommendations
    
    def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context for ranking decisions."""
        context = {
            'engagement_score': 0.0,
            'activity_level': 'low',
            'preferred_times': [],
            'recent_interactions': 0
        }
        
        with get_db_session() as db:
            # Get engagement metrics
            latest_metric = db.query(EngagementMetric).filter(
                EngagementMetric.user_id == user_id,
                EngagementMetric.metric_name == 'engagement_score'
            ).order_by(EngagementMetric.calculated_at.desc()).first()
            
            if latest_metric:
                context['engagement_score'] = latest_metric.metric_value
            
            # Get recent activity level
            recent_time = datetime.utcnow() - timedelta(days=7)
            recent_interactions = db.query(UserInteraction).filter(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= recent_time
            ).count()
            
            context['recent_interactions'] = recent_interactions
            
            if recent_interactions > 20:
                context['activity_level'] = 'high'
            elif recent_interactions > 5:
                context['activity_level'] = 'medium'
            
            # Analyze preferred interaction times
            interactions = db.query(UserInteraction).filter(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= recent_time
            ).all()
            
            if interactions:
                hours = [interaction.timestamp.hour for interaction in interactions]
                # Find most common hours (simple approach)
                hour_counts = {}
                for hour in hours:
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                
                # Get top 3 preferred hours
                preferred_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                context['preferred_times'] = [hour for hour, _ in preferred_hours]
        
        return context
    
    def _calculate_candidate_scores(self, user_id: str, candidate: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate individual scoring factors for a candidate."""
        scores = {}
        
        # Interest similarity (from matcher)
        scores['interest_similarity'] = candidate.get('similarity_score', candidate.get('recommendation_score', 0.0))
        
        # Engagement score alignment
        candidate_engagement = candidate.get('engagement_score', 0.5)
        user_engagement = user_context['engagement_score']
        engagement_diff = abs(candidate_engagement - user_engagement)
        scores['engagement_score'] = max(0.0, 1.0 - engagement_diff)
        
        # Recency (prefer recently active users)
        last_activity = candidate.get('last_activity')
        if last_activity:
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            
            days_since_activity = (datetime.utcnow() - last_activity.replace(tzinfo=None)).days
            scores['recency'] = max(0.0, 1.0 - (days_since_activity / 30.0))
        else:
            scores['recency'] = 0.5
        
        # Diversity (will be calculated later in batch)
        scores['diversity'] = 1.0
        
        # Feedback quality (based on mutual connections' feedback)
        scores['feedback_quality'] = self._estimate_feedback_quality(candidate.get('user_id', ''))
        
        return scores
    
    def _calculate_temporal_score(self, event: Dict[str, Any], user_context: Dict[str, Any]) -> float:
        """Calculate temporal relevance score for events."""
        event_time = event.get('start_time')
        if not event_time:
            return 0.5
        
        if isinstance(event_time, str):
            try:
                event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            except:
                return 0.5
        
        # Check if event time aligns with user's preferred times
        event_hour = event_time.hour
        preferred_times = user_context.get('preferred_times', [])
        
        if preferred_times and event_hour in preferred_times:
            return 1.0
        elif preferred_times:
            # Calculate distance to nearest preferred time
            min_distance = min(abs(event_hour - pref_hour) for pref_hour in preferred_times)
            return max(0.0, 1.0 - (min_distance / 12.0))
        
        return 0.5
    
    def _calculate_capacity_score(self, event: Dict[str, Any]) -> float:
        """Calculate capacity-based score (prefer events with availability)."""
        max_capacity = event.get('max_capacity', 100)
        current_attendees = event.get('current_attendees', 0)
        
        if max_capacity <= 0:
            return 0.5
        
        utilization = current_attendees / max_capacity
        
        # Prefer events that are not too empty or too full
        if 0.2 <= utilization <= 0.8:
            return 1.0
        elif utilization < 0.2:
            return 0.7  # Slightly penalize very empty events
        else:
            return max(0.0, 1.0 - utilization)  # Penalize very full events
    
    def _calculate_popularity_score(self, event: Dict[str, Any]) -> float:
        """Calculate popularity-based score."""
        attendees = event.get('current_attendees', 0)
        
        # Logarithmic scaling for popularity
        if attendees <= 0:
            return 0.1
        
        # Normalize using log scale
        popularity_score = math.log(attendees + 1) / math.log(101)  # Normalize to 0-1
        return min(1.0, popularity_score)
    
    def _apply_diversity_penalty(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply diversity penalty to avoid too similar recommendations."""
        if len(candidates) <= 1:
            return candidates
        
        # Calculate similarity between candidates based on shared interests
        for i, candidate in enumerate(candidates):
            diversity_penalty = 0.0
            candidate_interests = set(candidate.get('shared_interests', []))
            
            # Compare with higher-ranked candidates
            for j in range(i):
                other_candidate = candidates[j]
                other_interests = set(other_candidate.get('shared_interests', []))
                
                # Calculate overlap
                if candidate_interests and other_interests:
                    overlap = len(candidate_interests & other_interests) / len(candidate_interests | other_interests)
                    diversity_penalty += overlap * 0.1  # Small penalty for each similar candidate
            
            # Apply penalty
            original_score = candidate['final_score']
            candidate['final_score'] = max(0.0, original_score - diversity_penalty)
            candidate['diversity_penalty'] = diversity_penalty
        
        return candidates
    
    def _analyze_user_feedback_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's historical feedback patterns."""
        patterns = {
            'avg_rating': 3.0,
            'preferred_types': [],
            'disliked_types': [],
            'feedback_count': 0
        }
        
        with get_db_session() as db:
            feedback_items = db.query(FeedbackItem).filter(
                FeedbackItem.user_id == user_id
            ).all()
            
            if not feedback_items:
                return patterns
            
            patterns['feedback_count'] = len(feedback_items)
            
            # Calculate average rating
            ratings = [item.rating for item in feedback_items if item.rating is not None]
            if ratings:
                patterns['avg_rating'] = np.mean(ratings)
            
            # Analyze feedback by type
            type_ratings = {}
            for item in feedback_items:
                if item.rating is not None:
                    feedback_type = item.feedback_type
                    if feedback_type not in type_ratings:
                        type_ratings[feedback_type] = []
                    type_ratings[feedback_type].append(item.rating)
            
            # Identify preferred and disliked types
            for feedback_type, ratings in type_ratings.items():
                avg_rating = np.mean(ratings)
                if avg_rating >= 4.0:
                    patterns['preferred_types'].append(feedback_type)
                elif avg_rating <= 2.0:
                    patterns['disliked_types'].append(feedback_type)
        
        return patterns
    
    def _calculate_personalization_adjustment(self, recommendation: Dict[str, Any], feedback_patterns: Dict[str, Any]) -> float:
        """Calculate personalization adjustment factor."""
        adjustment = 1.0
        
        # Adjust based on user's rating patterns
        user_avg_rating = feedback_patterns['avg_rating']
        if user_avg_rating > 3.5:
            # User tends to rate highly, slightly boost all recommendations
            adjustment *= 1.1
        elif user_avg_rating < 2.5:
            # User tends to rate poorly, be more conservative
            adjustment *= 0.9
        
        # Adjust based on recommendation type preferences
        rec_type = recommendation.get('type', recommendation.get('recommendation_type', ''))
        if rec_type in feedback_patterns['preferred_types']:
            adjustment *= 1.2
        elif rec_type in feedback_patterns['disliked_types']:
            adjustment *= 0.7
        
        return adjustment
    
    def _estimate_feedback_quality(self, candidate_user_id: str) -> float:
        """Estimate likely feedback quality for a candidate user."""
        if not candidate_user_id:
            return 0.5
        
        with get_db_session() as db:
            # Get recent feedback about this user (if any)
            recent_time = datetime.utcnow() - timedelta(days=30)
            
            # This is a simplified approach - in practice, you'd have more sophisticated
            # feedback tracking between users
            feedback_count = db.query(FeedbackItem).filter(
                FeedbackItem.user_id == candidate_user_id,
                FeedbackItem.timestamp >= recent_time
            ).count()
            
            # Users who provide feedback tend to be more engaged
            if feedback_count > 5:
                return 0.8
            elif feedback_count > 0:
                return 0.6
            else:
                return 0.4
