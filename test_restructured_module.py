#!/usr/bin/env python3
"""
Test script to verify restructured LUKi Engagement Module functionality.
Tests the new modular architecture with data, graph, recommend, and interfaces layers.
"""

import sys
import traceback
from datetime import datetime, timedelta

def test_imports():
    """Test that all new module components can be imported."""
    print("Testing imports for restructured module...")
    try:
        # Test configuration
        from luki_modules_engagement import EngagementConfig
        
        # Test data layer
        from luki_modules_engagement.data import DataLoader, UserEventSchema, InteractionSchema, FeedbackSchema
        
        # Test graph layer
        from luki_modules_engagement.graph import GraphBuilder, GraphMetrics, GraphStore
        
        # Test recommendation layer
        from luki_modules_engagement.recommend import InterestMatcher, RecommendationRanker, RecommendationExplainer
        
        # Test interfaces layer
        from luki_modules_engagement.interfaces import EngagementAgentTools, EngagementAPI
        
        # Test legacy components (backward compatibility)
        from luki_modules_engagement import InteractionTracker, EngagementMetrics, FeedbackCollector, SocialGraphAnalyzer
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_data_layer():
    """Test data layer functionality."""
    print("\nTesting data layer...")
    try:
        from luki_modules_engagement.data import DataLoader, UserEventSchema
        
        # Test schema validation
        event_data = {
            'user_id': 'test_user_123',
            'event_type': 'test_event',
            'timestamp': datetime.utcnow(),
            'data': {'test': True},
            'context': {'source': 'test'}
        }
        
        event_schema = UserEventSchema(**event_data)
        print(f"✅ Schema validation successful: {event_schema.event_type}")
        
        # Test data loader instantiation
        loader = DataLoader()
        print("✅ DataLoader instantiated successfully")
        
        return True
    except Exception as e:
        print(f"❌ Data layer test failed: {e}")
        traceback.print_exc()
        return False

def test_graph_layer():
    """Test graph layer functionality."""
    print("\nTesting graph layer...")
    try:
        from luki_modules_engagement.graph import GraphBuilder, GraphMetrics, GraphStore
        
        # Test instantiation
        builder = GraphBuilder()
        metrics = GraphMetrics()
        store = GraphStore()
        
        print("✅ Graph components instantiated successfully")
        print(f"   GraphBuilder: {type(builder).__name__}")
        print(f"   GraphMetrics: {type(metrics).__name__}")
        print(f"   GraphStore: {type(store).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Graph layer test failed: {e}")
        traceback.print_exc()
        return False

def test_recommendation_layer():
    """Test recommendation layer functionality."""
    print("\nTesting recommendation layer...")
    try:
        from luki_modules_engagement.recommend import InterestMatcher, RecommendationRanker, RecommendationExplainer
        
        # Test instantiation
        matcher = InterestMatcher()
        ranker = RecommendationRanker()
        explainer = RecommendationExplainer()
        
        print("✅ Recommendation components instantiated successfully")
        print(f"   InterestMatcher: {type(matcher).__name__}")
        print(f"   RecommendationRanker: {type(ranker).__name__}")
        print(f"   RecommendationExplainer: {type(explainer).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Recommendation layer test failed: {e}")
        traceback.print_exc()
        return False

def test_interfaces_layer():
    """Test interfaces layer functionality."""
    print("\nTesting interfaces layer...")
    try:
        from luki_modules_engagement.interfaces import EngagementAgentTools, EngagementAPI
        
        # Test instantiation
        agent_tools = EngagementAgentTools()
        api = EngagementAPI()
        
        print("✅ Interface components instantiated successfully")
        print(f"   EngagementAgentTools: {type(agent_tools).__name__}")
        print(f"   EngagementAPI: {type(api).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Interfaces layer test failed: {e}")
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Test that legacy components still work."""
    print("\nTesting backward compatibility...")
    try:
        from luki_modules_engagement import InteractionTracker, EngagementMetrics, FeedbackCollector, SocialGraphAnalyzer
        from luki_modules_engagement.database import DatabaseManager
        
        # Test database setup
        db_manager = DatabaseManager()
        db_manager.create_tables()
        print("✅ Database tables created successfully")
        
        # Test legacy component instantiation
        tracker = InteractionTracker()
        metrics = EngagementMetrics()
        feedback = FeedbackCollector()
        social = SocialGraphAnalyzer()
        
        print("✅ Legacy components instantiated successfully")
        print(f"   InteractionTracker: {type(tracker).__name__}")
        print(f"   EngagementMetrics: {type(metrics).__name__}")
        print(f"   FeedbackCollector: {type(feedback).__name__}")
        print(f"   SocialGraphAnalyzer: {type(social).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """Test integration between layers."""
    print("\nTesting layer integration...")
    try:
        from luki_modules_engagement import EngagementConfig
        from luki_modules_engagement.data import DataLoader
        from luki_modules_engagement.graph import GraphBuilder
        from luki_modules_engagement.recommend import InterestMatcher
        
        # Test with shared config
        config = EngagementConfig()
        
        loader = DataLoader(config)
        builder = GraphBuilder(config)
        matcher = InterestMatcher(config)
        
        print("✅ Components initialized with shared config")
        print(f"   Database URL: {config.database_url}")
        print(f"   Tracking enabled: {config.enable_interaction_tracking}")
        
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests for the restructured module."""
    print("=" * 70)
    print("LUKi Engagement Module - Restructured Architecture Test Suite")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_data_layer,
        test_graph_layer,
        test_recommendation_layer,
        test_interfaces_layer,
        test_backward_compatibility,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 70)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The restructured engagement module is ready to use.")
        print("\n📋 New Architecture Summary:")
        print("   • data/ - ELR ingestion, schemas, data loading")
        print("   • graph/ - Social/interest graph building, metrics, storage")
        print("   • recommend/ - Interest matching, ranking, explanations")
        print("   • interfaces/ - LangChain tools, FastAPI endpoints")
        print("   • Legacy components maintained for backward compatibility")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("💡 Note: Import errors may be due to missing dependencies.")
        print("   Run: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
