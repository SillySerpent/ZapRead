"""
Bionic Intensity Management System

Provides intelligent, configurable bionic reading intensity based on
document structure, user preferences, and content analysis.
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from .document_analyzer import DocumentElement, DocumentAnalyzer


class IntensityLevel(Enum):
    """Predefined intensity levels for different use cases."""
    MINIMAL = 0.2      # Very subtle enhancement
    CONSERVATIVE = 0.3  # Safe for technical content
    STANDARD = 0.4     # Optimal for general reading
    ENHANCED = 0.5     # Stronger enhancement
    MAXIMUM = 0.6      # Very strong enhancement


class ReadingProfile(Enum):
    """Reading profiles for different user needs."""
    SPEED_READING = "speed_reading"        # Maximum enhancement for fast reading
    ACCESSIBILITY = "accessibility"        # Optimized for reading difficulties
    TECHNICAL = "technical"               # Conservative for technical documents
    STANDARD = "standard"                 # Balanced approach for general reading
    PRESERVATION = "preservation"         # Minimal changes, preserve original
    CUSTOM = "custom"                     # User-defined settings


class IntensityManager:
    """
    Manages bionic reading intensity based on content analysis and user preferences.
    """
    
    def __init__(self, profile: ReadingProfile = ReadingProfile.STANDARD):
        """
        Initialize the intensity manager.
        
        Args:
            profile: Default reading profile to use
        """
        self.profile = profile
        self.document_analyzer = DocumentAnalyzer()
        self.custom_settings = {}
        
        # Profile-based intensity mappings
        self.profile_intensities = {
            ReadingProfile.SPEED_READING: {
                DocumentElement.HEADING: 0.7,
                DocumentElement.PARAGRAPH: 0.6,
                DocumentElement.LIST_ITEM: 0.55,
                DocumentElement.CAPTION: 0.4,
                DocumentElement.QUOTE: 0.5,
                DocumentElement.TABLE_CELL: 0.3,
                DocumentElement.TECHNICAL_TERM: 0.0,
                DocumentElement.MATH_CONTENT: 0.0,
                DocumentElement.CODE: 0.0,
                DocumentElement.REFERENCE: 0.3,
            },
            ReadingProfile.ACCESSIBILITY: {
                DocumentElement.HEADING: 0.6,
                DocumentElement.PARAGRAPH: 0.5,
                DocumentElement.LIST_ITEM: 0.5,
                DocumentElement.CAPTION: 0.4,
                DocumentElement.QUOTE: 0.45,
                DocumentElement.TABLE_CELL: 0.35,
                DocumentElement.TECHNICAL_TERM: 0.0,
                DocumentElement.MATH_CONTENT: 0.0,
                DocumentElement.CODE: 0.0,
                DocumentElement.REFERENCE: 0.3,
            },
            ReadingProfile.STANDARD: {
                DocumentElement.HEADING: 0.5,
                DocumentElement.PARAGRAPH: 0.4,
                DocumentElement.LIST_ITEM: 0.4,
                DocumentElement.CAPTION: 0.3,
                DocumentElement.QUOTE: 0.35,
                DocumentElement.TABLE_CELL: 0.25,
                DocumentElement.TECHNICAL_TERM: 0.0,
                DocumentElement.MATH_CONTENT: 0.0,
                DocumentElement.CODE: 0.0,
                DocumentElement.REFERENCE: 0.2,
            },
            ReadingProfile.TECHNICAL: {
                DocumentElement.HEADING: 0.4,
                DocumentElement.PARAGRAPH: 0.3,
                DocumentElement.LIST_ITEM: 0.3,
                DocumentElement.CAPTION: 0.2,
                DocumentElement.QUOTE: 0.25,
                DocumentElement.TABLE_CELL: 0.2,
                DocumentElement.TECHNICAL_TERM: 0.0,
                DocumentElement.MATH_CONTENT: 0.0,
                DocumentElement.CODE: 0.0,
                DocumentElement.REFERENCE: 0.15,
            },
            ReadingProfile.PRESERVATION: {
                DocumentElement.HEADING: 0.3,
                DocumentElement.PARAGRAPH: 0.2,
                DocumentElement.LIST_ITEM: 0.2,
                DocumentElement.CAPTION: 0.15,
                DocumentElement.QUOTE: 0.15,
                DocumentElement.TABLE_CELL: 0.1,
                DocumentElement.TECHNICAL_TERM: 0.0,
                DocumentElement.MATH_CONTENT: 0.0,
                DocumentElement.CODE: 0.0,
                DocumentElement.REFERENCE: 0.1,
            },
        }
        
        # Custom profile (empty, filled by user)
        self.profile_intensities[ReadingProfile.CUSTOM] = {}
    
    def get_intensity_for_text(self, text: str, context: Optional[Dict] = None, 
                              override_profile: Optional[ReadingProfile] = None) -> Dict[str, Any]:
        """
        Get bionic intensity for specific text based on analysis and profile.
        
        Args:
            text: Text to analyze
            context: Optional context information
            override_profile: Profile to use instead of default
            
        Returns:
            Intensity analysis with recommended settings
        """
        # Analyze the text element
        analysis = self.document_analyzer.analyze_text_element(text, context)
        element_type = analysis['element_type']
        
        # Determine which profile to use
        active_profile = override_profile or self.profile
        
        # Get intensity based on profile
        if active_profile == ReadingProfile.CUSTOM:
            intensity = self.custom_settings.get(element_type, analysis['bionic_intensity'])
        else:
            intensity = self.profile_intensities.get(active_profile, {}).get(
                element_type, analysis['bionic_intensity']
            )
        
        # Apply document-level adjustments
        intensity = self._apply_context_adjustments(intensity, analysis, context)
        
        return {
            'intensity': intensity,
            'element_type': element_type,
            'should_process': analysis['should_process'] and intensity > 0,
            'preserve_formatting': analysis['preserve_formatting'],
            'special_handling': analysis['special_handling'],
            'font_weight_multiplier': analysis['font_weight_multiplier'],
            'confidence': self._calculate_confidence(analysis, context)
        }
    
    def _apply_context_adjustments(self, base_intensity: float, analysis: Dict, 
                                 context: Optional[Dict]) -> float:
        """
        Apply context-based adjustments to base intensity.
        
        Args:
            base_intensity: Base intensity from profile
            analysis: Element analysis results
            context: Optional context information
            
        Returns:
            Adjusted intensity value
        """
        adjusted_intensity = base_intensity
        
        if not context:
            return adjusted_intensity
        
        # Adjust based on font size
        font_size = context.get('font_size', 12)
        if font_size < 10:
            adjusted_intensity *= 0.8  # Reduce for small text
        elif font_size > 18:
            adjusted_intensity *= 1.1  # Increase for large text
        
        # Adjust based on text length
        text_length = context.get('text_length', 0)
        if text_length < 10:
            adjusted_intensity *= 0.9  # Reduce for very short text
        elif text_length > 200:
            adjusted_intensity *= 1.05  # Slightly increase for long text
        
        # Adjust based on document position
        position = context.get('position', 'middle')
        if position == 'beginning':
            adjusted_intensity *= 1.05  # Slightly more at document start
        elif position == 'end':
            adjusted_intensity *= 0.95  # Slightly less at document end
        
        # Keep within valid range
        return max(0.0, min(1.0, adjusted_intensity))
    
    def _calculate_confidence(self, analysis: Dict, context: Optional[Dict]) -> float:
        """
        Calculate confidence in the intensity recommendation.
        
        Args:
            analysis: Element analysis results
            context: Optional context information
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.8  # Base confidence
        
        # Increase confidence for clear element types
        element_type = analysis['element_type']
        high_confidence_types = {
            DocumentElement.HEADING,
            DocumentElement.CODE,
            DocumentElement.MATH_CONTENT,
            DocumentElement.TECHNICAL_TERM
        }
        
        if element_type in high_confidence_types:
            confidence = 0.95
        
        # Adjust based on context availability
        if context:
            if 'font_size' in context:
                confidence += 0.05
            if 'is_bold' in context:
                confidence += 0.05
            if 'position' in context:
                confidence += 0.03
        
        return min(1.0, confidence)
    
    def set_custom_intensity(self, element_type: DocumentElement, intensity: float):
        """
        Set custom intensity for specific element type.
        
        Args:
            element_type: Type of document element
            intensity: Intensity value (0.0 to 1.0)
        """
        if not 0.0 <= intensity <= 1.0:
            raise ValueError("Intensity must be between 0.0 and 1.0")
        
        self.custom_settings[element_type] = intensity
        self.profile = ReadingProfile.CUSTOM
    
    def get_custom_settings(self) -> Dict[DocumentElement, float]:
        """
        Get current custom intensity settings.
        
        Returns:
            Dictionary of custom intensity settings
        """
        return self.custom_settings.copy()
    
    def reset_to_profile(self, profile: ReadingProfile):
        """
        Reset to a predefined profile.
        
        Args:
            profile: Profile to switch to
        """
        self.profile = profile
        self.custom_settings.clear()
    
    def analyze_document_and_recommend(self, text_elements: List[Dict]) -> Dict[str, Any]:
        """
        Analyze entire document and recommend optimal intensity settings.
        
        Args:
            text_elements: List of text elements with content and metadata
            
        Returns:
            Document analysis with intensity recommendations
        """
        # Analyze document structure
        doc_analysis = self.document_analyzer.analyze_document_structure(text_elements)
        
        # Recommend profile based on document characteristics
        recommended_profile = self._recommend_profile_for_document(doc_analysis)
        
        # Calculate element-specific recommendations
        element_recommendations = []
        for element in text_elements:
            text = element.get('text', '')
            context = element.get('context', {})
            
            recommendation = self.get_intensity_for_text(
                text, context, recommended_profile
            )
            element_recommendations.append(recommendation)
        
        return {
            'document_analysis': doc_analysis,
            'recommended_profile': recommended_profile,
            'element_recommendations': element_recommendations,
            'processing_summary': self._create_processing_summary(element_recommendations),
            'quality_metrics': self._calculate_quality_metrics(element_recommendations)
        }
    
    def _recommend_profile_for_document(self, doc_analysis: Dict) -> ReadingProfile:
        """
        Recommend optimal profile based on document analysis.
        
        Args:
            doc_analysis: Document structure analysis
            
        Returns:
            Recommended reading profile
        """
        complexity_score = doc_analysis['complexity_score']
        type_distribution = doc_analysis['element_type_distribution']
        
        # Technical documents
        if (complexity_score > 0.6 or 
            doc_analysis['has_technical_content'] or 
            doc_analysis['has_math']):
            return ReadingProfile.TECHNICAL
        
        # Structured documents with lots of headings/lists
        if doc_analysis['has_headings'] and doc_analysis['has_lists']:
            if complexity_score < 0.3:
                return ReadingProfile.SPEED_READING
            else:
                return ReadingProfile.ACCESSIBILITY
        
        # Simple documents
        if complexity_score < 0.2:
            return ReadingProfile.SPEED_READING
        
        # Default to accessibility for mixed content
        return ReadingProfile.ACCESSIBILITY
    
    def _create_processing_summary(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """
        Create summary of processing recommendations.
        
        Args:
            recommendations: List of element recommendations
            
        Returns:
            Processing summary
        """
        total_elements = len(recommendations)
        elements_to_process = sum(1 for r in recommendations if r['should_process'])
        
        avg_intensity = sum(r['intensity'] for r in recommendations) / max(total_elements, 1)
        
        element_type_counts = {}
        for rec in recommendations:
            element_type = rec['element_type']
            element_type_counts[element_type] = element_type_counts.get(element_type, 0) + 1
        
        return {
            'total_elements': total_elements,
            'elements_to_process': elements_to_process,
            'processing_ratio': elements_to_process / max(total_elements, 1),
            'average_intensity': avg_intensity,
            'element_distribution': element_type_counts,
            'estimated_enhancement': self._estimate_reading_enhancement(avg_intensity, elements_to_process)
        }
    
    def _calculate_quality_metrics(self, recommendations: List[Dict]) -> Dict[str, float]:
        """
        Calculate quality metrics for processing recommendations.
        
        Args:
            recommendations: List of element recommendations
            
        Returns:
            Quality metrics
        """
        total_recs = len(recommendations)
        if total_recs == 0:
            return {'confidence': 0.0, 'consistency': 0.0, 'coverage': 0.0}
        
        # Average confidence
        avg_confidence = sum(r['confidence'] for r in recommendations) / total_recs
        
        # Consistency (low variance in similar element types)
        type_intensities = {}
        for rec in recommendations:
            element_type = rec['element_type']
            if element_type not in type_intensities:
                type_intensities[element_type] = []
            type_intensities[element_type].append(rec['intensity'])
        
        consistency_scores = []
        for intensities in type_intensities.values():
            if len(intensities) > 1:
                variance = sum((x - sum(intensities)/len(intensities))**2 for x in intensities) / len(intensities)
                consistency_scores.append(1.0 - min(variance, 1.0))
            else:
                consistency_scores.append(1.0)
        
        consistency = sum(consistency_scores) / max(len(consistency_scores), 1)
        
        # Coverage (percentage of elements that will be processed)
        processable = sum(1 for r in recommendations if r['should_process'])
        coverage = processable / total_recs
        
        return {
            'confidence': avg_confidence,
            'consistency': consistency,
            'coverage': coverage
        }
    
    def _estimate_reading_enhancement(self, avg_intensity: float, elements_processed: int) -> Dict[str, Any]:
        """
        Estimate reading speed enhancement based on intensity and coverage.
        
        Args:
            avg_intensity: Average intensity across processed elements
            elements_processed: Number of elements to be processed
            
        Returns:
            Enhancement estimates
        """
        # Rough estimates based on bionic reading research
        base_improvement = avg_intensity * 0.15  # Up to 15% improvement
        coverage_factor = min(elements_processed / 100, 1.0)  # Diminishing returns
        
        estimated_improvement = base_improvement * coverage_factor
        
        return {
            'estimated_speed_improvement': estimated_improvement,
            'estimated_comprehension_impact': max(0, estimated_improvement - 0.05),
            'confidence_level': 'high' if avg_intensity > 0.4 else 'medium' if avg_intensity > 0.2 else 'low'
        }
    
    def export_settings(self) -> Dict[str, Any]:
        """
        Export current intensity settings for persistence.
        
        Returns:
            Exportable settings dictionary
        """
        return {
            'profile': self.profile.value,
            'custom_settings': {elem.value: intensity for elem, intensity in self.custom_settings.items()},
            'version': '1.0'
        }
    
    def import_settings(self, settings: Dict[str, Any]):
        """
        Import intensity settings from dictionary.
        
        Args:
            settings: Settings dictionary to import
        """
        try:
            # Import profile
            profile_value = settings.get('profile', ReadingProfile.ACCESSIBILITY.value)
            self.profile = ReadingProfile(profile_value)
            
            # Import custom settings
            custom_settings = settings.get('custom_settings', {})
            self.custom_settings = {
                DocumentElement(elem): intensity 
                for elem, intensity in custom_settings.items()
                if 0.0 <= intensity <= 1.0
            }
            
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid settings format: {e}")
    
    def get_profile_description(self, profile: ReadingProfile) -> str:
        """
        Get human-readable description of a profile.
        
        Args:
            profile: Profile to describe
            
        Returns:
            Description string
        """
        descriptions = {
            ReadingProfile.SPEED_READING: "Optimized for fast reading with strong enhancement",
            ReadingProfile.ACCESSIBILITY: "Balanced enhancement suitable for most users",
            ReadingProfile.TECHNICAL: "Conservative enhancement preserving technical content",
            ReadingProfile.PRESERVATION: "Minimal changes while maintaining document integrity",
            ReadingProfile.CUSTOM: "User-defined intensity settings"
        }
        
        return descriptions.get(profile, "Unknown profile") 