"""
Recommendation explanation system for LUKi engagement module.
Provides transparent, human-readable explanations for AI recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RecommendationExplainer:
    """
    Provides transparent explanations for user, event, and community recommendations.
    """
    
    def __init__(self, config=None):
        """Initialize the recommendation explainer."""
        self.config = config
        self.explanation_templates = {
            'user': {
                'interest_match': "You both enjoy {interests}",
                'activity_similarity': "You've both participated in {activities}",
                'demographic_match': "You share similar {demographics}",
                'social_connection': "You have {count} mutual connections"
            },
            'event': {
                'interest_alignment': "This matches your interests in {interests}",
                'past_participation': "You've enjoyed similar {event_types} before",
                'social_factor': "{friend_count} of your connections are attending",
                'timing_factor': "Perfect timing for your {availability} schedule"
            },
            'community': {
                'shared_interests': "Members share your passion for {interests}",
                'activity_level': "Active community with {activity_count} recent activities",
                'size_factor': "Right size community ({member_count} members)",
                'engagement_level': "High engagement with {engagement_score}% participation"
            }
        }
    
    def explain_user_recommendation(self, user_id: str, recommended_user: Dict[str, Any], 
                                  match_factors: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate explanation for user recommendation.
        
        Args:
            user_id: Target user ID
            recommended_user: Recommended user data
            match_factors: Factors contributing to the match
            
        Returns:
            Explanation with reasons and visual elements
        """
        try:
            explanations = []
            visual_elements = []
            
            # Interest-based explanations
            if 'interest_similarity' in match_factors and match_factors['interest_similarity'] > 0.5:
                common_interests = recommended_user.get('common_interests', [])
                if common_interests:
                    explanations.append(
                        self.explanation_templates['user']['interest_match'].format(
                            interests=', '.join(common_interests[:3])
                        )
                    )
                    visual_elements.append({
                        'type': 'interest_overlap',
                        'data': common_interests[:5]
                    })
            
            # Activity-based explanations
            if 'activity_similarity' in match_factors and match_factors['activity_similarity'] > 0.4:
                common_activities = recommended_user.get('common_activities', [])
                if common_activities:
                    explanations.append(
                        self.explanation_templates['user']['activity_similarity'].format(
                            activities=', '.join(common_activities[:2])
                        )
                    )
            
            # Social connection explanations
            mutual_connections = recommended_user.get('mutual_connections', 0)
            if mutual_connections > 0:
                explanations.append(
                    self.explanation_templates['user']['social_connection'].format(
                        count=mutual_connections
                    )
                )
                visual_elements.append({
                    'type': 'social_network',
                    'data': {'mutual_count': mutual_connections}
                })
            
            return {
                'user_id': recommended_user.get('user_id'),
                'name': recommended_user.get('name', 'Unknown'),
                'explanations': explanations,
                'visual_elements': visual_elements,
                'confidence_score': sum(match_factors.values()) / len(match_factors) if match_factors else 0.0,
                'match_factors': match_factors,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error explaining user recommendation: {e}")
            return {
                'user_id': recommended_user.get('user_id'),
                'explanations': ['Recommended based on profile compatibility'],
                'visual_elements': [],
                'confidence_score': 0.5,
                'error': str(e)
            }
    
    def explain_event_recommendation(self, user_id: str, event: Dict[str, Any], 
                                   match_factors: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate explanation for event recommendation.
        
        Args:
            user_id: Target user ID
            event: Event data
            match_factors: Factors contributing to the match
            
        Returns:
            Explanation with reasons and visual elements
        """
        try:
            explanations = []
            visual_elements = []
            
            # Interest alignment
            if 'interest_match' in match_factors and match_factors['interest_match'] > 0.5:
                event_interests = event.get('interests', [])
                if event_interests:
                    explanations.append(
                        self.explanation_templates['event']['interest_alignment'].format(
                            interests=', '.join(event_interests[:3])
                        )
                    )
            
            # Past participation
            if 'historical_preference' in match_factors and match_factors['historical_preference'] > 0.4:
                event_type = event.get('type', 'activity')
                explanations.append(
                    self.explanation_templates['event']['past_participation'].format(
                        event_types=event_type
                    )
                )
            
            # Social factors
            attending_friends = event.get('attending_friends', 0)
            if attending_friends > 0:
                explanations.append(
                    self.explanation_templates['event']['social_factor'].format(
                        friend_count=attending_friends
                    )
                )
                visual_elements.append({
                    'type': 'social_attendance',
                    'data': {'friend_count': attending_friends}
                })
            
            # Timing factors
            if 'timing_score' in match_factors and match_factors['timing_score'] > 0.6:
                availability = event.get('time_preference', 'preferred')
                explanations.append(
                    self.explanation_templates['event']['timing_factor'].format(
                        availability=availability
                    )
                )
            
            return {
                'event_id': event.get('event_id'),
                'title': event.get('title', 'Event'),
                'explanations': explanations,
                'visual_elements': visual_elements,
                'confidence_score': sum(match_factors.values()) / len(match_factors) if match_factors else 0.0,
                'match_factors': match_factors,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error explaining event recommendation: {e}")
            return {
                'event_id': event.get('event_id'),
                'explanations': ['Recommended based on your interests and preferences'],
                'visual_elements': [],
                'confidence_score': 0.5,
                'error': str(e)
            }
    
    def explain_community_recommendation(self, user_id: str, community: Dict[str, Any], 
                                       match_factors: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate explanation for community recommendation.
        
        Args:
            user_id: Target user ID
            community: Community data
            match_factors: Factors contributing to the match
            
        Returns:
            Explanation with reasons and visual elements
        """
        try:
            explanations = []
            visual_elements = []
            
            # Shared interests
            if 'interest_overlap' in match_factors and match_factors['interest_overlap'] > 0.5:
                community_interests = community.get('primary_interests', [])
                if community_interests:
                    explanations.append(
                        self.explanation_templates['community']['shared_interests'].format(
                            interests=', '.join(community_interests[:3])
                        )
                    )
            
            # Activity level
            activity_count = community.get('recent_activity_count', 0)
            if activity_count > 5:
                explanations.append(
                    self.explanation_templates['community']['activity_level'].format(
                        activity_count=activity_count
                    )
                )
                visual_elements.append({
                    'type': 'activity_timeline',
                    'data': {'activity_count': activity_count}
                })
            
            # Community size
            member_count = community.get('member_count', 0)
            if 10 <= member_count <= 100:  # Sweet spot for engagement
                explanations.append(
                    self.explanation_templates['community']['size_factor'].format(
                        member_count=member_count
                    )
                )
            
            # Engagement level
            engagement_score = community.get('engagement_score', 0)
            if engagement_score > 70:
                explanations.append(
                    self.explanation_templates['community']['engagement_level'].format(
                        engagement_score=engagement_score
                    )
                )
            
            return {
                'community_id': community.get('community_id'),
                'name': community.get('name', 'Community'),
                'explanations': explanations,
                'visual_elements': visual_elements,
                'confidence_score': sum(match_factors.values()) / len(match_factors) if match_factors else 0.0,
                'match_factors': match_factors,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error explaining community recommendation: {e}")
            return {
                'community_id': community.get('community_id'),
                'explanations': ['Recommended based on community compatibility'],
                'visual_elements': [],
                'confidence_score': 0.5,
                'error': str(e)
            }
    
    def generate_batch_explanations(self, recommendations: List[Dict[str, Any]], 
                                  recommendation_type: str) -> List[Dict[str, Any]]:
        """
        Generate explanations for a batch of recommendations.
        
        Args:
            recommendations: List of recommendations with match factors
            recommendation_type: Type of recommendations ('user', 'event', 'community')
            
        Returns:
            List of explanations
        """
        explanations = []
        
        for rec in recommendations:
            try:
                target_user_id = rec.get('target_user_id')
                recommended_item = rec.get('recommended_item')
                match_factors = rec.get('match_factors', {})
                
                # Validate required fields and convert types safely
                if not target_user_id or not recommended_item:
                    explanation = {
                        'error': 'Missing required fields: target_user_id or recommended_item',
                        'explanations': ['Unable to generate explanation'],
                        'confidence_score': 0.0
                    }
                elif recommendation_type == 'user':
                    explanation = self.explain_user_recommendation(
                        str(target_user_id),
                        dict(recommended_item) if isinstance(recommended_item, dict) else {},
                        match_factors
                    )
                elif recommendation_type == 'event':
                    explanation = self.explain_event_recommendation(
                        str(target_user_id),
                        dict(recommended_item) if isinstance(recommended_item, dict) else {},
                        match_factors
                    )
                elif recommendation_type == 'community':
                    explanation = self.explain_community_recommendation(
                        str(target_user_id),
                        dict(recommended_item) if isinstance(recommended_item, dict) else {},
                        match_factors
                    )
                else:
                    explanation = {
                        'error': f'Unknown recommendation type: {recommendation_type}',
                        'explanations': ['Unable to generate explanation'],
                        'confidence_score': 0.0
                    }
                
                explanations.append(explanation)
                
            except Exception as e:
                logger.error(f"Error in batch explanation: {e}")
                explanations.append({
                    'error': str(e),
                    'explanations': ['Unable to generate explanation'],
                    'confidence_score': 0.0
                })
        
        return explanations
