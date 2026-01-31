import re

class ActionParser:
    """
    Parses natural language text to extract roleplay actions (text within *asterisks*).
    """
    
    @staticmethod
    def extract_actions(text):
        """
        Extracts actions from the text.
        Returns a list of action strings found between asterisks.
        
        Example: 
        Input: "*looks down* I am sorry."
        Output: ["looks down"]
        """
        if not text:
            return []
            
        # Regex to find content between asterisks: *action*
        # Non-greedy match (.*?) to handle multiple actions in one string
        pattern = r'\*(.*?)\*'
        actions = re.findall(pattern, text)
        
        # Clean up whitespace
        return [action.strip() for action in actions if action.strip()]

    @staticmethod
    def remove_actions(text):
        """
        Removes actions from the text, leaving only the spoken part.
        Useful for TTS if we don't want the voice to read the actions.
        """
        if not text:
            return ""
            
        pattern = r'\*.*?\*'
        clean_text = re.sub(pattern, '', text)
        return clean_text.strip()
