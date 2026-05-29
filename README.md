# CPTutor for Sublime Text

CPTutor is a Sublime Text 4 plugin that integrates Google's Gemini AI to assist you with Competitive Programming. It provides a dedicated chat interface, context-aware assistance, and automatic code updates.

## Features

- **Dedicated Chat Panel**: Chat with Gemini in a split-view layout.
- **Context Awareness**: Automatically includes open files in the prompt for better understanding.
- **Auto Code Update**: Gemini can suggest changes to your files, which you can apply with a single click.
- **Google Login Mode**: Use your existing `gemini` CLI session to bypass API key limits.
- **API Key Mode**: Use your own Google AI Studio API key.

## Installation

1. Clone this repository into your Sublime Text `Packages` directory:
   ```bash
   cd ~/.config/sublime-text/Packages
   git clone https://github.com/YOUR_USERNAME/CPTutor.git
   ```
2. (Optional) Install the Gemini CLI for Google Login mode:
   ```bash
   npm install -g @google/gemini-cli
   gemini login
   ```

## Usage

- Open the Command Palette (`Ctrl+Shift+P`) and type `CPTutor: Start`.
- Type your question directly in the `CPTutor Chat` tab and press `Ctrl+Enter`.
- Use `CPTutor: Toggle Google Login (CLI Mode)` to switch between API Key and CLI session.

## Configuration

Settings can be found in `Preferences -> Package Settings -> CPTutor -> Settings`.

## License

MIT
