from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QTabWidget, QWidget, QFormLayout, 
    QMessageBox, QCheckBox, QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt
import os
from core.settings.settings_manager import SettingsManager
from core.config import Config
from core.automation.automation_manager import AutomationManager
from core.live2d.resource_manager import Live2DResourceManager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_manager = SettingsManager()
        self.automation_manager = AutomationManager()
        self.setWindowTitle("SpecsAI Settings")
        self.resize(650, 600)
        
        # Apply Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border-radius: 5px;
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #aaa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0063b1;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #3b3b3b;
                color: #aaa;
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #2b2b2b;
                color: #fff;
                border-bottom: 2px solid #0078d7;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Initialize Tabs
        self.init_ai_tab()
        self.init_voice_tab()
        self.init_character_tab()
        self.init_system_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save & Apply")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background-color: #555;")
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        self.layout.addLayout(button_layout)
        
        self.load_current_settings()

    def init_ai_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # --- Provider Selection ---
        provider_group = QGroupBox("AI Provider")
        provider_layout = QFormLayout()
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "SpecsAI (Default/Recommended)", 
            "Google Gemini (Free/Paid)", 
            "Groq (Fastest/Free Beta)", 
            "Sambanova (Fast/Free)",
            "Hugging Face (Free Inference)",
            "Claude (Anthropic)",
            "Ollama (Local)", 
            "OpenAI (Paid)"
        ])
        self.provider_combo.currentIndexChanged.connect(self.toggle_provider_settings)
        
        provider_layout.addRow("Active Brain:", self.provider_combo)
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # --- AI Personality / Role ---
        persona_group = QGroupBox("AI Personality & Role")
        persona_layout = QFormLayout()
        
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Default (Helpful Assistant & Mature)", 
            "Romantic (Affectionate Partner)", 
            "Friendly (Best Friend/Casual)", 
            "Girlfriend (Loving & Possessive)", 
            "Boyfriend (Protective & Caring)", 
            "Fun (Witty Entertainer)", 
            "Mature (Wise Mentor)"
        ])
        # Map friendly names to internal keys
        self.role_map = {
            0: "default", 1: "romantic", 2: "friendly", 3: "girlfriend", 
            4: "boyfriend", 5: "fun", 6: "mature"
        }
        
        persona_layout.addRow("Current Persona:", self.role_combo)
        persona_group.setLayout(persona_layout)
        layout.addWidget(persona_group)

        # --- SpecsAI Settings ---
        self.specsai_group = QGroupBox("SpecsAI Engine (Advanced)")
        specsai_layout = QFormLayout()
        info_label = QLabel("Powered by the proprietary SpecsAI Neural Core™, engineered by SpecsXR. This advanced high-technology engine is designed for next-level intelligence and lightning-fast performance.\nA unique, adaptive, and future-ready AI experience designed exclusively for you.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #00aaff; font-style: italic; font-weight: bold;")
        specsai_layout.addRow(info_label)
        self.specsai_group.setLayout(specsai_layout)
        layout.addWidget(self.specsai_group)
        
        # --- Gemini Settings ---
        self.gemini_group = QGroupBox("Google Gemini Settings")
        gemini_layout = QFormLayout()
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setPlaceholderText("Enter API Key")
        self.gemini_key_input.setEchoMode(QLineEdit.Password)
        self.gemini_model_input = QLineEdit("gemini-1.5-flash")
        
        gemini_layout.addRow("API Key (Optional):", self.gemini_key_input)
        gemini_layout.addRow("Model Name:", self.gemini_model_input)
        
        # Link to get key
        link_label = QLabel('<a href="https://aistudio.google.com/app/apikey" style="color: #0078d7;">Get Free API Key Here</a>')
        link_label.setOpenExternalLinks(True)
        gemini_layout.addRow("", link_label)
        
        self.gemini_group.setLayout(gemini_layout)
        layout.addWidget(self.gemini_group)

        # --- Groq Settings ---
        self.groq_group = QGroupBox("Groq Settings (Super Fast)")
        groq_layout = QFormLayout()
        self.groq_key_input = QLineEdit()
        self.groq_key_input.setPlaceholderText("Enter Groq API Key")
        self.groq_key_input.setEchoMode(QLineEdit.Password)
        self.groq_model_input = QLineEdit("llama-3.3-70b-versatile")
        
        groq_layout.addRow("API Key:", self.groq_key_input)
        groq_layout.addRow("Model Name:", self.groq_model_input)
        
        groq_link = QLabel('<a href="https://console.groq.com/keys" style="color: #0078d7;">Get Free Groq Key</a>')
        groq_link.setOpenExternalLinks(True)
        groq_layout.addRow("", groq_link)
        
        self.groq_group.setLayout(groq_layout)
        layout.addWidget(self.groq_group)

        # --- Sambanova Settings ---
        self.sambanova_group = QGroupBox("Sambanova Settings (Fast/Free)")
        sambanova_layout = QFormLayout()
        self.sambanova_key_input = QLineEdit()
        self.sambanova_key_input.setPlaceholderText("Enter Sambanova API Key")
        self.sambanova_key_input.setEchoMode(QLineEdit.Password)
        self.sambanova_model_input = QLineEdit("Meta-Llama-3.1-70B-Instruct")
        
        sambanova_layout.addRow("API Key:", self.sambanova_key_input)
        sambanova_layout.addRow("Model Name:", self.sambanova_model_input)
        
        sambanova_link = QLabel('<a href="https://cloud.sambanova.ai/" style="color: #0078d7;">Get Free Sambanova Key</a>')
        sambanova_link.setOpenExternalLinks(True)
        sambanova_layout.addRow("", sambanova_link)
        
        self.sambanova_group.setLayout(sambanova_layout)
        layout.addWidget(self.sambanova_group)

        # --- Hugging Face Settings ---
        self.huggingface_group = QGroupBox("Hugging Face Settings (Free Inference)")
        huggingface_layout = QFormLayout()
        self.huggingface_key_input = QLineEdit()
        self.huggingface_key_input.setPlaceholderText("Enter Hugging Face Token")
        self.huggingface_key_input.setEchoMode(QLineEdit.Password)
        self.huggingface_model_input = QLineEdit("meta-llama/Meta-Llama-3-8B-Instruct")
        
        huggingface_layout.addRow("Access Token:", self.huggingface_key_input)
        huggingface_layout.addRow("Model ID:", self.huggingface_model_input)
        
        hf_link = QLabel('<a href="https://huggingface.co/settings/tokens" style="color: #0078d7;">Get HF Token</a>')
        hf_link.setOpenExternalLinks(True)
        huggingface_layout.addRow("", hf_link)
        
        self.huggingface_group.setLayout(huggingface_layout)
        layout.addWidget(self.huggingface_group)
        
        # --- Claude Settings ---
        self.claude_group = QGroupBox("Claude Settings (Anthropic)")
        claude_layout = QFormLayout()
        self.claude_key_input = QLineEdit()
        self.claude_key_input.setPlaceholderText("Enter Claude API Key")
        self.claude_key_input.setEchoMode(QLineEdit.Password)
        self.claude_model_input = QLineEdit("claude-3-5-sonnet-20240620")
        
        claude_layout.addRow("API Key:", self.claude_key_input)
        claude_layout.addRow("Model Name:", self.claude_model_input)
        
        claude_link = QLabel('<a href="https://console.anthropic.com/settings/keys" style="color: #0078d7;">Get Claude Key</a>')
        claude_link.setOpenExternalLinks(True)
        claude_layout.addRow("", claude_link)
        
        self.claude_group.setLayout(claude_layout)
        layout.addWidget(self.claude_group)

        # --- Ollama Settings ---
        self.ollama_group = QGroupBox("Ollama (Local) Settings")
        ollama_layout = QFormLayout()
        self.ollama_url_input = QLineEdit("http://localhost:11434")
        self.ollama_model_input = QLineEdit("llama3")
        
        ollama_layout.addRow("Base URL:", self.ollama_url_input)
        ollama_layout.addRow("Model Name:", self.ollama_model_input)
        self.ollama_group.setLayout(ollama_layout)
        layout.addWidget(self.ollama_group)
        
        # --- OpenAI Settings ---
        self.openai_group = QGroupBox("OpenAI Settings")
        openai_layout = QFormLayout()
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.Password)
        self.openai_model_input = QLineEdit("gpt-4o-mini")
        
        openai_layout.addRow("API Key:", self.openai_key_input)
        openai_layout.addRow("Model Name:", self.openai_model_input)
        self.openai_group.setLayout(openai_layout)
        layout.addWidget(self.openai_group)

        layout.addStretch()
        self.tabs.addTab(tab, "AI Brain")

    def init_voice_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        voice_group = QGroupBox("Character Voice")
        voice_layout = QFormLayout()
        
        self.voice_combo = QComboBox()
        
        # Populate voices
        self.available_voices = []
        if self.parent() and hasattr(self.parent(), 'voice_service') and self.parent().voice_service:
            voices = self.parent().voice_service.get_available_voices()
            # Sort voices: Presets first, then others
            presets = [v for v in voices if v.provider == "edge-tts-preset"]
            others = [v for v in voices if v.provider != "edge-tts-preset"]
            
            # Sort presets by category/style
            presets.sort(key=lambda x: (x.style or "", x.name))
            
            self.available_voices = presets + others
            
            for v in self.available_voices:
                # Add friendly name
                display_name = v.name
                if v.provider == "edge-tts-preset":
                    display_name = f"⭐ {v.name}"
                self.voice_combo.addItem(display_name, v.id)
                
        voice_layout.addRow("Select Voice:", self.voice_combo)
        
        # Add some info about selected voice
        self.voice_info_label = QLabel("Select a voice to see details.")
        self.voice_info_label.setWordWrap(True)
        self.voice_combo.currentIndexChanged.connect(self.update_voice_info)
        
        voice_layout.addRow(self.voice_info_label)
        
        # Strict Voice Mode
        self.strict_voice_chk = QCheckBox("Strict Voice Mode (Disable Auto-Switch)")
        self.strict_voice_chk.setToolTip("If checked, the selected voice will be used for ALL languages.\nUncheck to allow auto-switching to a native voice for better pronunciation.")
        voice_layout.addRow(self.strict_voice_chk)
        
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Voice")

    def update_voice_info(self):
        idx = self.voice_combo.currentIndex()
        if idx >= 0 and idx < len(self.available_voices):
            v = self.available_voices[idx]
            info = f"Gender: {v.gender}\nProvider: {v.provider}\nLanguage: {v.language}"
            if v.provider == "edge-tts-preset":
                info += f"\nStyle: {v.style}\nPitch: {v.pitch}, Rate: {v.rate}"
            self.voice_info_label.setText(info)

    def init_character_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # --- Import Section ---
        import_group = QGroupBox("Import New Character")
        import_layout = QVBoxLayout()
        
        lbl = QLabel("Upload a Live2D Model Folder or ZIP.\nThe system will automatically analyze, repair, and configure it for you.")
        lbl.setWordWrap(True)
        import_layout.addWidget(lbl)
        
        btn_layout = QHBoxLayout()
        self.import_btn = QPushButton("📂 Select Model Folder/Zip")
        self.import_btn.clicked.connect(self.handle_import_character)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addStretch()
        
        import_layout.addLayout(btn_layout)
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # --- Active Character Section ---
        char_group = QGroupBox("Active Character")
        char_layout = QFormLayout()
        
        self.character_combo = QComboBox()
        # Populate with existing characters
        self.populate_characters()
        
        char_layout.addRow("Current Model:", self.character_combo)
        
        self.char_info_label = QLabel("Select a character to see details.")
        self.char_info_label.setStyleSheet("color: #aaa; font-style: italic;")
        char_layout.addRow(self.char_info_label)
        
        char_group.setLayout(char_layout)
        layout.addWidget(char_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Character")

    def populate_characters(self):
        self.character_combo.clear()
        # Scan assets/character
        import os
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        char_dir = os.path.join(root_dir, "assets", "character")
        
        if os.path.exists(char_dir):
            for name in os.listdir(char_dir):
                path = os.path.join(char_dir, name)
                if os.path.isdir(path):
                    # Check if valid Live2D model (heuristic)
                    if any(f.endswith(".moc3") for f in os.listdir(path)) or \
                       any(f.endswith(".model3.json") for f in os.listdir(path)) or \
                       os.path.exists(os.path.join(path, "runtime")): # Some have runtime folder
                        self.character_combo.addItem(name, name)
                        
            # Also check User folder
            user_char_dir = os.path.join(char_dir, "User")
            if os.path.exists(user_char_dir):
                for name in os.listdir(user_char_dir):
                     self.character_combo.addItem(f"User: {name}", f"User/{name}")

    def handle_import_character(self):
        path = QFileDialog.getExistingDirectory(self, "Select Character Folder")
        if not path:
            return
            
        try:
            # 1. Import
            new_path = self.automation_manager.import_character_package(path)
            if not new_path:
                QMessageBox.warning(self, "Import Failed", "Could not import the character package.")
                return
                
            # 2. Analyze & Repair
            QMessageBox.information(self, "Analyzing", "Analyzing and configuring model... This may take a moment.")
            
            res_manager = Live2DResourceManager()
            res_manager.load_resources(new_path)
            
            caps = res_manager.capabilities
            report = f"Import Successful!\n\nPhysics: {'✅' if caps['physics'] else '❌'}\nLipSync: {'✅' if caps['lipsync'] else '❌'}\nAuto-Generated Config: {'⚠️ Yes' if caps['generated_json'] else 'No'}"
            
            QMessageBox.information(self, "Setup Complete", report)
            
            # 3. Refresh List
            self.populate_characters()
            
            # Select the new one
            index = self.character_combo.findData(f"User/{os.path.basename(new_path)}")
            if index >= 0:
                self.character_combo.setCurrentIndex(index)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def init_system_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        system_group = QGroupBox("Window Settings")
        sys_layout = QFormLayout()
        
        # Language Selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto", "English", "Bangla", "Hindi"])
        self.language_combo.setToolTip("Select the language you want to speak/type in.\nAuto will detect English/Bangla/Hindi automatically.")
        
        sys_layout.addRow("Language Mode:", self.language_combo)
        
        self.always_on_top_chk = QCheckBox("Always On Top")
        self.transparent_chk = QCheckBox("Transparent Background")
        
        sys_layout.addRow(self.always_on_top_chk)
        sys_layout.addRow(self.transparent_chk)
        
        system_group.setLayout(sys_layout)
        layout.addWidget(system_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "System")

    def toggle_provider_settings(self):
        index = self.provider_combo.currentIndex()
        # 0: SpecsAI, 1: Gemini, 2: Groq, 3: Sambanova, 4: Hugging Face, 5: Claude, 6: Ollama, 7: OpenAI
        self.specsai_group.setVisible(index == 0)
        self.gemini_group.setVisible(index == 1)
        self.groq_group.setVisible(index == 2)
        self.sambanova_group.setVisible(index == 3)
        self.huggingface_group.setVisible(index == 4)
        self.claude_group.setVisible(index == 5)
        self.ollama_group.setVisible(index == 6)
        self.openai_group.setVisible(index == 7)

    def load_current_settings(self):
        settings = self.settings_manager.get_all()
        ai = settings.get("ai", {})
        sys = settings.get("system", {})
        
        # Character
        current_char = sys.get("character_model", "shoujo_a")
        # Find in combo
        index = self.character_combo.findData(current_char)
        if index >= 0:
            self.character_combo.setCurrentIndex(index)
        
        # Provider
        # Map provider string to combo index
        provider_map = {
            "auto": 0,      # SpecsAI
            "gemini": 1, 
            "groq": 2, 
            "sambanova": 3,
            "huggingface": 4,
            "claude": 5, 
            "ollama": 6, 
            "openai": 7
        }
        # Default to "auto" (SpecsAI) if not set or unknown
        current_provider = ai.get("provider", "auto")
        self.provider_combo.setCurrentIndex(provider_map.get(current_provider, 0))
        
        # Gemini
        self.gemini_key_input.setText(ai.get("gemini_api_key", ""))
        self.gemini_model_input.setText(ai.get("gemini_model", "gemini-1.5-flash"))
        
        # Groq
        self.groq_key_input.setText(ai.get("groq_api_key", ""))
        self.groq_model_input.setText(ai.get("groq_model", "llama-3.3-70b-versatile"))

        # Sambanova
        self.sambanova_key_input.setText(ai.get("sambanova_api_key", ""))
        self.sambanova_model_input.setText(ai.get("sambanova_model", "Meta-Llama-3.1-70B-Instruct"))

        # Hugging Face
        self.huggingface_key_input.setText(ai.get("huggingface_api_key", ""))
        self.huggingface_model_input.setText(ai.get("huggingface_model", "meta-llama/Meta-Llama-3-8B-Instruct"))

        # Claude
        self.claude_key_input.setText(ai.get("claude_api_key", ""))
        self.claude_model_input.setText(ai.get("claude_model", "claude-3-5-sonnet-20240620"))
        
        # Ollama
        self.ollama_url_input.setText(ai.get("ollama_url", "http://localhost:11434"))
        self.ollama_model_input.setText(ai.get("ollama_model", "llama3"))
        
        # OpenAI
        self.openai_key_input.setText(ai.get("openai_api_key", ""))
        self.openai_model_input.setText(ai.get("openai_model", "gpt-4o-mini"))
        
        # Personality / Role
        # Map internal keys to combo index
        current_role = ai.get("role", "default")
        # Find index for role
        for idx, key in self.role_map.items():
            if key == current_role:
                self.role_combo.setCurrentIndex(idx)
                break
        
        # System
        self.always_on_top_chk.setChecked(sys.get("always_on_top", True))
        self.transparent_chk.setChecked(sys.get("transparent_mode", True))
        
        # Language
        current_lang = sys.get("language", "Auto")
        index = self.language_combo.findText(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        self.toggle_provider_settings()

        # Voice
        voice_settings = settings.get("voice", {})
        saved_voice_id = voice_settings.get("default_voice_id")
        if self.available_voices:
            # Find index
            for i, v in enumerate(self.available_voices):
                if v.id == saved_voice_id:
                    self.voice_combo.setCurrentIndex(i)
                    break
        
        # Strict Voice Mode
        self.strict_voice_chk.setChecked(voice_settings.get("strict_mode", False))

    def save_settings(self):
        try:
            provider_idx = self.provider_combo.currentIndex()
            # 0: SpecsAI (auto), 1: Gemini, 2: Groq, 3: Sambanova, 4: HF, 5: Claude, 6: Ollama, 7: OpenAI
            provider_map = {
                0: "auto", 
                1: "gemini", 
                2: "groq", 
                3: "sambanova",
                4: "huggingface",
                5: "claude", 
                6: "ollama", 
                7: "openai"
            }
            
            # Safe text retrieval helper
            def get_text(widget):
                return widget.text().strip() if hasattr(widget, 'text') else ""

            ai_settings = {
                "provider": provider_map.get(provider_idx, "gemini"),
                "gemini_api_key": get_text(self.gemini_key_input),
                "gemini_model": get_text(self.gemini_model_input),
                "groq_api_key": get_text(self.groq_key_input),
                "groq_model": get_text(self.groq_model_input),
                "sambanova_api_key": get_text(self.sambanova_key_input),
                "sambanova_model": get_text(self.sambanova_model_input),
                "huggingface_api_key": get_text(self.huggingface_key_input),
                "huggingface_model": get_text(self.huggingface_model_input),
                "claude_api_key": get_text(self.claude_key_input),
                "claude_model": get_text(self.claude_model_input),
                "ollama_url": get_text(self.ollama_url_input),
                "ollama_model": get_text(self.ollama_model_input),
                "openai_api_key": get_text(self.openai_key_input),
                "openai_model": get_text(self.openai_model_input)
            }
            
            sys_settings = {
                "always_on_top": self.always_on_top_chk.isChecked(),
                "transparent_mode": self.transparent_chk.isChecked(),
                "language": self.language_combo.currentText(),
                "character_model": self.character_combo.currentData()
            }
            
            # Save settings safely using .get() to prevent KeyError
            self.settings_manager.set("ai", "provider", ai_settings.get("provider", "auto"))
            self.settings_manager.set("ai", "gemini_api_key", ai_settings.get("gemini_api_key", ""))
            self.settings_manager.set("ai", "gemini_model", ai_settings.get("gemini_model", ""))
            self.settings_manager.set("ai", "groq_api_key", ai_settings.get("groq_api_key", ""))
            self.settings_manager.set("ai", "groq_model", ai_settings.get("groq_model", ""))
            self.settings_manager.set("ai", "sambanova_api_key", ai_settings.get("sambanova_api_key", ""))
            self.settings_manager.set("ai", "sambanova_model", ai_settings.get("sambanova_model", ""))
            self.settings_manager.set("ai", "huggingface_api_key", ai_settings.get("huggingface_api_key", ""))
            self.settings_manager.set("ai", "huggingface_model", ai_settings.get("huggingface_model", ""))
            self.settings_manager.set("ai", "claude_api_key", ai_settings.get("claude_api_key", ""))
            self.settings_manager.set("ai", "claude_model", ai_settings.get("claude_model", ""))
            self.settings_manager.set("ai", "ollama_url", ai_settings.get("ollama_url", ""))
            self.settings_manager.set("ai", "ollama_model", ai_settings.get("ollama_model", ""))
            self.settings_manager.set("ai", "openai_api_key", ai_settings.get("openai_api_key", ""))
            self.settings_manager.set("ai", "openai_model", ai_settings.get("openai_model", ""))
            
            # Save Role / Persona
            try:
                role_idx = self.role_combo.currentIndex()
                role_key = self.role_map.get(role_idx, "default")
                self.settings_manager.set("ai", "role", role_key)
            except Exception as e:
                print(f"Error saving role: {e}")
            
            self.settings_manager.set("system", "always_on_top", sys_settings["always_on_top"])
            self.settings_manager.set("system", "transparent_mode", sys_settings["transparent_mode"])
            self.settings_manager.set("system", "language", sys_settings["language"])
            
            # Update Global Config Immediately
            Config.LANGUAGE_MODE = sys_settings["language"]
            
            # Save Voice
            try:
                voice_id = self.voice_combo.currentData()
                strict_mode = self.strict_voice_chk.isChecked()
                
                self.settings_manager.set("voice", "default_voice_id", voice_id)
                self.settings_manager.set("voice", "strict_mode", strict_mode)
                
                # Apply voice
                if self.parent() and hasattr(self.parent(), 'voice_service') and self.parent().voice_service:
                    self.parent().voice_service.set_voice(voice_id)
                    # Apply strict mode to service
                    if hasattr(self.parent().voice_service, 'set_strict_mode'):
                        self.parent().voice_service.set_strict_mode(strict_mode)
            except Exception as e:
                print(f"Error saving voice: {e}")

            # Apply AI Mood
            if self.parent() and hasattr(self.parent(), 'apply_ai_settings'):
                 self.parent().apply_ai_settings()
            
            QMessageBox.information(self, "Success", "Settings saved successfully!\nSome changes may require a restart.")
            self.accept()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
