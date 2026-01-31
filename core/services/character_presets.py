from dataclasses import dataclass
from typing import Dict, List

@dataclass
class CharacterProfile:
    id: str
    name: str
    category: str  # "anime" or "real"
    base_voice_id: str  # Edge TTS voice ID
    pitch: str = "+0Hz"  # e.g., "+20Hz", "-10Hz"
    rate: str = "+0%"   # e.g., "+10%", "-5%"
    volume: str = "+0%"
    description: str = ""

class CharacterPresets:
    @staticmethod
    def get_presets() -> List[CharacterProfile]:
        presets = []
        
        # --- Anime Characters (50) ---
        # High pitch, fast, energetic for females; Deep/Cool for males
        
        # Female Anime
        anime_females = [
            ("Anime: Energetic Heroine", "en-US-AvaNeural", "+25Hz", "+10%"),
            ("Anime: Tsundere Girl", "en-US-MichelleNeural", "+30Hz", "+15%"),
            ("Anime: Shy Student", "en-US-AnaNeural", "+15Hz", "-5%"),
            ("Anime: Magical Girl", "en-GB-MaisieNeural", "+35Hz", "+10%"),
            ("Anime: Big Sister (Onee-san)", "en-US-EmmaNeural", "+5Hz", "+0%"),
            ("Anime: Robot Girl", "en-US-AnaNeural", "+50Hz", "+5%"),
            ("Anime: Childhood Friend", "en-AU-NatashaNeural", "+20Hz", "+5%"),
            ("Anime: Battle Princess", "en-CA-ClaraNeural", "+10Hz", "+20%"),
            ("Anime: Mysterious Loli", "zh-CN-XiaoxiaoNeural", "+10Hz", "+5%"), # Chinese voice speaking English often sounds very anime-like
            ("Anime: Idol Singer", "ja-JP-NanamiNeural", "+10Hz", "+5%"), # Japanese voice
            ("Anime: Ninja Girl", "en-US-JennyNeural", "+15Hz", "+25%"),
            ("Anime: Demon Queen", "en-GB-SoniaNeural", "-10Hz", "+5%"),
            ("Anime: Fairy Companion", "en-PH-RosaNeural", "+40Hz", "+15%"),
            ("Anime: Student Council Pres", "en-US-AriaNeural", "+10Hz", "+5%"),
            ("Anime: Yandere", "en-US-GuyNeural", "+60Hz", "+10%"), # Experiment: High pitch male sometimes sounds uncanny female
            ("Anime: Cat Girl", "ja-JP-NanamiNeural", "+25Hz", "+15%"),
            ("Anime: Elf Archer", "en-IE-EmilyNeural", "+20Hz", "+10%"),
            ("Anime: Spirit Guide", "en-NZ-MollyNeural", "+15Hz", "-5%"),
            ("Anime: Mecha Pilot", "en-SG-LunaNeural", "+10Hz", "+20%"),
            ("Anime: Shrine Maiden", "ja-JP-NanamiNeural", "+0Hz", "+0%"),
            ("Anime: Isekai Goddess", "en-US-MichelleNeural", "+15Hz", "-10%"),
            ("Anime: Guild Receptionist", "en-GB-LibbyNeural", "+20Hz", "+5%"),
            ("Anime: Dark Sorceress", "en-US-GuyNeural", "+50Hz", "-5%"),
            ("Anime: Chibi Mascot", "zh-CN-XiaoxiaoNeural", "+40Hz", "+20%"),
            ("Anime: Gamer Girl", "en-US-AnaNeural", "+20Hz", "+15%")
        ]
        
        # Male Anime
        anime_males = [
            ("Anime: Shonen Protagonist", "en-US-GuyNeural", "+15Hz", "+20%"),
            ("Anime: Cool Rival", "en-US-ChristopherNeural", "-10Hz", "+5%"),
            ("Anime: Wise Sensei", "en-US-RogerNeural", "-20Hz", "-10%"),
            ("Anime: Villain Overlord", "en-US-EricNeural", "-30Hz", "-15%"),
            ("Anime: Loyal Butler", "en-GB-RyanNeural", "-5Hz", "+0%"),
            ("Anime: Funny Sidekick", "en-US-GuyNeural", "+30Hz", "+25%"),
            ("Anime: Mech Commander", "en-US-ChristopherNeural", "-15Hz", "+10%"),
            ("Anime: Dark Avenger", "en-US-EricNeural", "-20Hz", "+5%"),
            ("Anime: Gentle Prince", "en-GB-ThomasNeural", "+5Hz", "-5%"),
            ("Anime: Berserker", "en-US-GuyNeural", "-10Hz", "+40%"),
            ("Anime: Strategist", "en-US-RogerNeural", "-5Hz", "+5%"),
            ("Anime: Samurai", "ja-JP-KeitaNeural", "-10Hz", "-5%"),
            ("Anime: Ninja Assassin", "en-HK-SamNeural", "-5Hz", "+15%"),
            ("Anime: High School Delinquent", "en-US-GuyNeural", "-5Hz", "+10%"),
            ("Anime: Isekai Hero", "en-US-ChristopherNeural", "+5Hz", "+10%"),
            ("Anime: Demon King", "en-US-EricNeural", "-40Hz", "-10%"),
            ("Anime: Space Pirate", "en-AU-WilliamNeural", "-10Hz", "+5%"),
            ("Anime: Cyborg", "en-US-SteffanNeural", "-5Hz", "+0%"),
            ("Anime: Beast Man", "en-KE-ChilembaNeural", "-30Hz", "+5%"),
            ("Anime: Trap Character", "en-US-GuyNeural", "+40Hz", "+10%"), # Feminine male
            ("Anime: Quiet Loner", "en-US-ChristopherNeural", "-5Hz", "-10%"),
            ("Anime: Hot-blooded Brawler", "en-US-GuyNeural", "+10Hz", "+30%"),
            ("Anime: Mysterious Transfer Student", "en-GB-RyanNeural", "+0Hz", "+0%"),
            ("Anime: Class President (Male)", "en-US-RogerNeural", "+5Hz", "+5%"),
            ("Anime: Talking Pet", "en-TZ-ElimuNeural", "+30Hz", "+10%")
        ]

        # --- Real Life Characters (50) ---
        
        # Famous Archetypes / Celebrity-likes (Approximations)
        real_life = [
            # Male
            ("Real: Deep Movie Trailer", "en-US-EricNeural", "-35Hz", "-10%"),
            ("Real: Tech Billionaire (Elon-ish)", "en-ZA-LeahNeural", "-20Hz", "+5%"), # Using specific accent
            ("Real: British Documentarian (Attenborough-ish)", "en-GB-RyanNeural", "-15Hz", "-10%"),
            ("Real: Morgan-like Narrator", "en-US-ChristopherNeural", "-25Hz", "-15%"),
            ("Real: Jarvis AI", "en-GB-RyanNeural", "+0Hz", "+0%"),
            ("Real: News Anchor (Male)", "en-US-RogerNeural", "-5Hz", "+5%"),
            ("Real: Late Night Host", "en-US-GuyNeural", "-5Hz", "+10%"),
            ("Real: Motivational Speaker", "en-US-EricNeural", "-10Hz", "+15%"),
            ("Real: Friendly Neighbor", "en-US-GuyNeural", "+0Hz", "+0%"),
            ("Real: Grumpy Old Man", "en-US-RogerNeural", "-20Hz", "-20%"),
            ("Real: Surfer Dude", "en-US-GuyNeural", "+5Hz", "-10%"),
            ("Real: Cowboy", "en-US-ChristopherNeural", "-15Hz", "-5%"),
            ("Real: Gangster", "en-US-EricNeural", "-20Hz", "+5%"),
            ("Real: Professor", "en-GB-ThomasNeural", "-10Hz", "-5%"),
            ("Real: Butler", "en-GB-RyanNeural", "-5Hz", "-5%"),
            ("Real: Drill Sergeant", "en-US-EricNeural", "-10Hz", "+30%"),
            ("Real: Hip Hop Artist", "en-US-GuyNeural", "-10Hz", "+15%"),
            ("Real: Southern Gentleman", "en-US-ChristopherNeural", "-5Hz", "-15%"),
            ("Real: New York Taxi Driver", "en-US-RogerNeural", "-10Hz", "+20%"),
            ("Real: Meditation Guide (Male)", "en-IN-PrabhatNeural", "-10Hz", "-20%"),
            ("Real: Tech Support (Indian)", "en-IN-PrabhatNeural", "+5Hz", "+5%"),
            ("Real: Australian Explorer", "en-AU-WilliamNeural", "-5Hz", "+10%"),
            ("Real: Irish Pub Owner", "en-IE-ConnorNeural", "-10Hz", "+5%"),
            ("Real: Scottish Warrior", "en-GB-RyanNeural", "-20Hz", "+10%"), # Approx
            ("Real: Russian Bad Guy", "ru-RU-DmitryNeural", "-20Hz", "-5%"), # Speaking English with accent (if supported) or just deep
            
            # Female
            ("Real: AI Assistant (Siri-like)", "en-US-AriaNeural", "+5Hz", "+5%"),
            ("Real: News Anchor (Female)", "en-US-JennyNeural", "+0Hz", "+5%"),
            ("Real: Soothing Therapist", "en-US-MichelleNeural", "-5Hz", "-10%"),
            ("Real: Valley Girl", "en-US-AnaNeural", "+15Hz", "+10%"),
            ("Real: British Royal", "en-GB-SoniaNeural", "+0Hz", "-5%"),
            ("Real: Southern Belle", "en-US-MichelleNeural", "+5Hz", "-15%"),
            ("Real: Karen", "en-US-AmberNeural", "+10Hz", "+5%"),
            ("Real: Tired Mom", "en-US-ElizabethNeural", "-5Hz", "-5%"),
            ("Real: Energetic Vlogger", "en-US-SaraNeural", "+15Hz", "+20%"),
            ("Real: Noir Femme Fatale", "en-US-MonicaNeural", "-10Hz", "-5%"),
            ("Real: French Fashionista", "fr-FR-DeniseNeural", "+0Hz", "+0%"), # Speaking English
            ("Real: Grandma", "en-US-ElizabethNeural", "-10Hz", "-20%"),
            ("Real: Strict Teacher", "en-GB-LibbyNeural", "-5Hz", "+0%"),
            ("Real: Whisper ASMR", "en-US-JaneNeural", "+0Hz", "-10%"), # Adjusted for stability
            ("Real: Pop Star", "en-US-JennyNeural", "+10Hz", "+10%"),
            ("Real: Corporate CEO", "en-US-AriaNeural", "-5Hz", "+0%"),
            ("Real: Sci-Fi Ship Computer", "en-GB-AbbiNeural", "+5Hz", "+0%"),
            ("Real: GPS Navigation", "en-US-AriaNeural", "+0Hz", "-5%"),
            ("Real: Horror Ghost", "en-US-AnaNeural", "+50Hz", "-50%"),
            ("Real: Telephone Operator", "en-US-NancyNeural", "+5Hz", "+5%"),
            ("Real: Yoga Instructor", "en-US-MichelleNeural", "-5Hz", "-15%"),
            ("Real: Fast Food Worker", "en-US-SaraNeural", "+5Hz", "+15%"),
            ("Real: Librarian", "en-US-AmberNeural", "-5Hz", "-10%"),
            ("Real: Child (Girl)", "en-US-AnaNeural", "+30Hz", "+5%"),
            ("Real: Child (Boy)", "en-US-GuyNeural", "+40Hz", "+10%")
        ]

        # Helper to create objects
        def create_list(source, cat):
            res = []
            for name, voice, pitch, rate in source:
                pid = name.lower().replace(" ", "_").replace(":", "").replace("(", "").replace(")", "")
                res.append(CharacterProfile(pid, name, cat, voice, pitch, rate))
            return res

        presets.extend(create_list(anime_females, "anime"))
        presets.extend(create_list(anime_males, "anime"))
        presets.extend(create_list(real_life, "real"))
        
        return presets
