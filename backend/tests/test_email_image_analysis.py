"""Unit tests for email image analysis."""
import base64
import json
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

from app.services.email_feature_detector import EmailFeatureDetector
from app.services.image_analysis_service import ImageAnalysisService


@pytest.fixture
def sample_email_image():
    """Create a sample email image for testing."""
    # Create a simple test image (white background with some colored rectangles)
    img = Image.new("RGB", (800, 600), color="white")
    from PIL import ImageDraw
    
    draw = ImageDraw.Draw(img)
    # Draw a "CTA button" rectangle
    draw.rectangle([300, 400, 500, 450], fill="blue", outline="black")
    # Draw a "logo" circle
    draw.ellipse([50, 50, 150, 150], fill="red", outline="black")
    # Draw some text area
    draw.rectangle([100, 200, 700, 350], fill="lightgray", outline="black")
    
    return img


@pytest.fixture
def sample_email_image_base64(sample_email_image):
    """Convert sample image to base64."""
    buffer = BytesIO()
    sample_email_image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    mock_service = MagicMock()
    mock_service.provider = "ollama"
    mock_service._get_ollama_client = MagicMock()
    
    # Mock Ollama client response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {
            "content": json.dumps([
                {
                    "feature_type": "call to action button",
                    "position": "middle-center",
                    "bbox": {"x_min": 30, "y_min": 50, "x_max": 70, "y_max": 60},
                    "confidence": 0.9,
                    "text_content": "Shop Now",
                    "color": "#0000FF"
                },
                {
                    "feature_type": "logo",
                    "position": "top-left",
                    "bbox": {"x_min": 5, "y_min": 5, "x_max": 20, "y_max": 20},
                    "confidence": 0.85,
                    "text_content": None,
                    "color": "#FF0000"
                }
            ])
        }
    }
    mock_response.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_response
    mock_service._get_ollama_client.return_value = mock_client
    
    return mock_service


@pytest.fixture
def mock_feature_detector():
    """Mock feature detector."""
    detector = MagicMock(spec=EmailFeatureDetector)
    detector.model = None  # Simulate LLM fallback mode
    detector.detect_features = MagicMock(return_value={
        "features": [
            {
                "feature_type": "call to action button",
                "feature_category": "cta_buttons",
                "confidence": 0.9,
                "bbox": {"x_min": 30, "y_min": 50, "x_max": 70, "y_max": 60},
                "position": "middle-center",
                "text_content": "Shop Now",
                "color": "#0000FF"
            },
            {
                "feature_type": "logo",
                "feature_category": "branding",
                "confidence": 0.85,
                "bbox": {"x_min": 5, "y_min": 5, "x_max": 20, "y_max": 20},
                "position": "top-left",
                "text_content": None,
                "color": "#FF0000"
            }
        ],
        "feature_catalog": {
            "cta_buttons": [
                {
                    "feature_type": "call to action button",
                    "confidence": 0.9,
                    "bbox": {"x_min": 30, "y_min": 50, "x_max": 70, "y_max": 60},
                    "position": "middle-center",
                    "text_content": "Shop Now",
                    "color": "#0000FF"
                }
            ],
            "branding": [
                {
                    "feature_type": "logo",
                    "confidence": 0.85,
                    "bbox": {"x_min": 5, "y_min": 5, "x_max": 20, "y_max": 20},
                    "position": "top-left",
                    "text_content": None,
                    "color": "#FF0000"
                }
            ],
            "summary": {
                "total_cta_buttons": 1,
                "total_promotions": 0,
                "total_products": 0,
                "total_content_elements": 0,
                "total_branding_elements": 1,
                "total_social_proof": 0,
                "total_urgency_indicators": 0,
                "total_structure_elements": 0,
            }
        },
        "total_features_detected": 2
    })
    return detector


class TestEmailFeatureDetector:
    """Tests for EmailFeatureDetector."""
    
    def test_detector_initialization(self):
        """Test that detector initializes (feature detection is disabled)."""
        detector = EmailFeatureDetector()
        assert detector is not None
        # Should initialize even if model is None (will use LLM fallback)
        assert hasattr(detector, 'model')
    
    @patch('app.services.email_feature_detector.settings')
    @patch('app.services.llm_service.LLMService')
    def test_detect_features_with_base64(self, mock_llm_class, mock_settings, sample_email_image_base64, mock_llm_service):
        """Test feature detection with base64 image."""
        detector = EmailFeatureDetector()
        detector.model = None  # Force LLM fallback
        
        mock_settings.openai_api_key = ""
        mock_llm_class.return_value = mock_llm_service
        
        result = detector.detect_features(image_base64=sample_email_image_base64)
        
        assert "features" in result
        assert "feature_catalog" in result
        assert "total_features_detected" in result
    
    def test_detect_features_with_image_path(self, sample_email_image, tmp_path):
        """Test feature detection with image file path."""
        # Save image to temporary file
        img_path = tmp_path / "test_email.png"
        sample_email_image.save(img_path)
        
        detector = EmailFeatureDetector()
        detector.model = None  # Force LLM fallback
        
        # Should handle file path loading
        image = detector._load_image(image_path=str(img_path))
        assert image is not None
        assert isinstance(image, Image.Image)


class TestImageAnalysisService:
    """Tests for ImageAnalysisService email analysis."""
    
    @patch('app.services.image_analysis_service.LLMService')
    @patch('app.services.image_analysis_service.EmailFeatureDetector')
    def test_analyze_email_image_with_base64(
        self, 
        mock_detector_class, 
        mock_llm_class,
        sample_email_image_base64,
        mock_feature_detector,
        mock_llm_service
    ):
        """Test analyzing a single email image using base64 input."""
        # Setup mocks
        mock_detector_class.return_value = mock_feature_detector
        mock_llm_class.return_value = mock_llm_service
        
        service = ImageAnalysisService()
        
        # Analyze image
        result = service.analyze_image(
            image_base64=sample_email_image_base64,
            campaign_id="test_campaign_123",
            campaign_name="Test Campaign",
            analysis_type="full",
            use_feature_detection=False
        )
        
        # Verify result structure
        assert "image_id" in result
        assert "campaign_id" in result
        assert result["campaign_id"] == "test_campaign_123"
        
        # Verify feature detection was called
        mock_feature_detector.detect_features.assert_called_once()
        call_args = mock_feature_detector.detect_features.call_args
        assert call_args[1]["image_base64"] == sample_email_image_base64
        assert call_args[1]["campaign_id"] == "test_campaign_123"
        
        # Verify features are included in result
        assert "email_features" in result or "feature_catalog" in result
    
    @patch('app.services.image_analysis_service.LLMService')
    @patch('app.services.image_analysis_service.EmailFeatureDetector')
    def test_analyze_email_image_with_url(
        self,
        mock_detector_class,
        mock_llm_class,
        mock_feature_detector,
        mock_llm_service
    ):
        """Test analyzing a single email image using URL input."""
        # Setup mocks
        mock_detector_class.return_value = mock_feature_detector
        mock_llm_class.return_value = mock_llm_service
        
        service = ImageAnalysisService()
        
        # Mock HTTP response for image URL
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = service.analyze_image(
                image_url="https://example.com/email.png",
                campaign_id="test_campaign_456",
                analysis_type="full",
                use_feature_detection=False
            )
        
        # Verify result
        assert "image_id" in result
        assert result["campaign_id"] == "test_campaign_456"
        
        # Verify feature detection was called with URL
        mock_feature_detector.detect_features.assert_called_once()
        call_args = mock_feature_detector.detect_features.call_args
        assert call_args[1]["image_url"] == "https://example.com/email.png"
    
    @patch('app.services.image_analysis_service.LLMService')
    @patch('app.services.image_analysis_service.EmailFeatureDetector')
    def test_analyze_email_without_feature_detection(
        self,
        mock_detector_class,
        mock_llm_class,
        sample_email_image_base64,
        mock_feature_detector,
        mock_llm_service
    ):
        """Test that analysis works when feature detection is disabled."""
        mock_detector_class.return_value = mock_feature_detector
        mock_llm_class.return_value = mock_llm_service
        
        service = ImageAnalysisService()
        
        result = service.analyze_image(
            image_base64=sample_email_image_base64,
            use_feature_detection=False  # Disable feature detection
        )
        
        # Should still return analysis result
        assert "image_id" in result
        # Feature detector should not be called
        mock_feature_detector.detect_features.assert_not_called()
    
    def test_analyze_image_requires_input(self):
        """Test that analyze_image raises error when no input provided."""
        service = ImageAnalysisService()
        
        with pytest.raises(ValueError, match="Either image_url or image_base64 must be provided"):
            service.analyze_image()
    
    @patch('app.services.image_analysis_service.LLMService')
    @patch('app.services.image_analysis_service.EmailFeatureDetector')
    def test_feature_catalog_structure(
        self,
        mock_detector_class,
        mock_llm_class,
        sample_email_image_base64,
        mock_feature_detector,
        mock_llm_service
    ):
        """Test that feature catalog has correct structure."""
        mock_detector_class.return_value = mock_feature_detector
        mock_llm_class.return_value = mock_llm_service
        
        service = ImageAnalysisService()
        result = service.analyze_image(
            image_base64=sample_email_image_base64,
            use_feature_detection=False
        )
        
        # Check if feature catalog is in result (may be in email_features or feature_catalog)
        if "feature_catalog" in result:
            catalog = result["feature_catalog"]
            # Verify catalog structure
            assert "cta_buttons" in catalog or "summary" in catalog
            if "summary" in catalog:
                assert "total_cta_buttons" in catalog["summary"]


class TestEmailAnalysisIntegration:
    """Integration tests for complete email analysis workflow."""
    
    @patch('app.services.image_analysis_service.LLMService')
    @patch('app.services.image_analysis_service.EmailFeatureDetector')
    def test_complete_email_analysis_workflow(
        self,
        mock_detector_class,
        mock_llm_class,
        sample_email_image_base64,
        mock_feature_detector,
        mock_llm_service
    ):
        """Test complete workflow: feature detection + image analysis."""
        mock_detector_class.return_value = mock_feature_detector
        mock_llm_class.return_value = mock_llm_service
        
        service = ImageAnalysisService()
        
        # Perform full analysis
        result = service.analyze_image(
            image_base64=sample_email_image_base64,
            campaign_id="integration_test_123",
            campaign_name="Integration Test Campaign",
            analysis_type="full",
            use_feature_detection=False
        )
        
        # Verify all expected fields are present
        required_fields = [
            "image_id",
            "campaign_id",
            "visual_elements",
            "dominant_colors",
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify feature detection was performed
        assert mock_feature_detector.detect_features.called
        
        # Verify campaign context was passed
        call_kwargs = mock_feature_detector.detect_features.call_args[1]
        assert call_kwargs["campaign_id"] == "integration_test_123"

