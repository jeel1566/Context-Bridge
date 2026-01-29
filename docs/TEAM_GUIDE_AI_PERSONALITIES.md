# 🧑‍💻 Team Member Guide: AI Personality Profiles

> **Assigned To:** Team Member 1
> **Estimated Time:** 2-3 days
> **Dependencies:** None - can start immediately!

---

## 🎯 Feature Overview

**What is this?** AI Personality Profiles are pre-configured prompts/personas that modify how the captured context is formatted and styled when injected into different AI platforms.

**Example Personas:**
- `senior-dev` - Technical, precise, code-focused
- `mentor` - Patient, educational, explains concepts
- `creative` - Imaginative, exploratory, open-ended
- `concise` - Brief, to the point, minimal output

**Why?** Different conversations need different tones. A code review should use `senior-dev`, while learning a new concept might need `mentor`.

---

## 📁 Project Structure Overview

```
Context Bridge/
├── backend/                    # Azure Functions (Python)
│   ├── agents/                 # ADK Agents - NOT YOUR FOCUS
│   ├── services/
│   │   └── encryption.py       # NOT YOUR FOCUS
│   └── ...
│
├── extension/                  # Chrome Extension (Your work area)
│   ├── src/
│   │   ├── sidepanel/          # Side panel UI
│   │   │   ├── index.html      # ← Add personality selector UI here
│   │   │   ├── index.js        # ← Add selector logic here
│   │   │   └── styles.css      # ← Add selector styles here
│   │   │
│   │   ├── config/             # ← CREATE THIS FOLDER
│   │   │   └── personalities.json  # ← CREATE THIS FILE
│   │   │
│   │   └── content-scripts/    # NOT YOUR FOCUS
│   │
│   └── manifest.json
│
└── docs/
```

---

## 📋 Your Tasks

### Task 1: Create Personalities Config File

**Create:** `extension/src/config/personalities.json`

```json
{
  "personalities": [
    {
      "id": "senior-dev",
      "name": "Senior Developer",
      "icon": "👨‍💻",
      "description": "Technical, precise, code-focused responses",
      "systemPrompt": "You are a senior software developer with 10+ years of experience. Be technical, precise, and focus on best practices. Provide code examples when relevant.",
      "tags": ["code", "technical", "review"]
    },
    {
      "id": "mentor",
      "name": "Patient Mentor",
      "icon": "🎓",
      "description": "Educational, explains concepts step by step",
      "systemPrompt": "You are a patient coding mentor. Explain concepts clearly, use analogies, and break down complex topics into digestible parts. Encourage the learner.",
      "tags": ["learning", "education", "beginner"]
    },
    {
      "id": "architect",
      "name": "System Architect",
      "icon": "🏗️",
      "description": "High-level design, scalability, patterns",
      "systemPrompt": "You are a system architect. Focus on high-level design, scalability, design patterns, and trade-offs. Think about long-term maintainability.",
      "tags": ["architecture", "design", "scale"]
    },
    {
      "id": "debugger",
      "name": "Debug Expert",
      "icon": "🔍",
      "description": "Systematic debugging, root cause analysis",
      "systemPrompt": "You are a debugging expert. Methodically analyze issues, suggest diagnostic steps, and find root causes. Be systematic and thorough.",
      "tags": ["debug", "troubleshoot", "fix"]
    },
    {
      "id": "creative",
      "name": "Creative Thinker",
      "icon": "🎨",
      "description": "Exploratory, innovative, outside the box",
      "systemPrompt": "You are a creative problem solver. Think outside the box, suggest unconventional solutions, and explore possibilities. Be imaginative.",
      "tags": ["creative", "brainstorm", "innovate"]
    },
    {
      "id": "concise",
      "name": "Straight to Point",
      "icon": "⚡",
      "description": "Brief, no explanations, just answers",
      "systemPrompt": "Be extremely concise. Give direct answers without explanations unless asked. Prioritize brevity over detail.",
      "tags": ["quick", "brief", "fast"]
    }
  ],
  "defaultPersonality": "senior-dev"
}
```

---

### Task 2: Add Personality Selector UI

**Modify:** `extension/src/sidepanel/index.html`

Add this section after the "Capture Panel" section (around line 35):

```html
<!-- Personality Selector -->
<section id="personality-panel" class="panel">
  <h2>🎭 AI Personality</h2>
  <div id="personality-selector" class="personality-grid">
    <!-- Will be populated by JS -->
  </div>
</section>
```

---

### Task 3: Add Personality Selector CSS

**Add to:** `extension/src/sidepanel/styles.css`

```css
/* Personality Selector */
.personality-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.personality-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  background: var(--bg);
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.personality-card:hover {
  background: var(--bg-hover);
  transform: translateY(-2px);
}

.personality-card.selected {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
}

.personality-card .icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.personality-card .name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}

.personality-card .description {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
}
```

---

### Task 4: Add Personality Selector Logic

**Modify:** `extension/src/sidepanel/index.js`

Add these functions:

```javascript
// ============================================
// Personality Selector
// ============================================

let personalities = [];
let selectedPersonality = 'senior-dev';

async function loadPersonalities() {
  try {
    const response = await fetch(chrome.runtime.getURL('src/config/personalities.json'));
    const data = await response.json();
    personalities = data.personalities;
    selectedPersonality = localStorage.getItem('selectedPersonality') || data.defaultPersonality;
    renderPersonalitySelector();
  } catch (error) {
    console.error('Failed to load personalities:', error);
  }
}

function renderPersonalitySelector() {
  const container = document.getElementById('personality-selector');
  if (!container) return;

  container.innerHTML = personalities.map(p => `
    <div class="personality-card ${p.id === selectedPersonality ? 'selected' : ''}" 
         data-personality-id="${p.id}">
      <span class="icon">${p.icon}</span>
      <span class="name">${p.name}</span>
      <span class="description">${p.description}</span>
    </div>
  `).join('');

  // Add click handlers
  container.querySelectorAll('.personality-card').forEach(card => {
    card.addEventListener('click', () => selectPersonality(card.dataset.personalityId));
  });
}

function selectPersonality(id) {
  selectedPersonality = id;
  localStorage.setItem('selectedPersonality', id);
  
  // Update UI
  document.querySelectorAll('.personality-card').forEach(card => {
    card.classList.toggle('selected', card.dataset.personalityId === id);
  });

  // Notify background script
  chrome.runtime.sendMessage({
    type: 'SET_PERSONALITY',
    data: { personalityId: id }
  });
}

function getSelectedPersonality() {
  return personalities.find(p => p.id === selectedPersonality);
}

// Call on init
loadPersonalities();
```

---

### Task 5: Update manifest.json for config access

**Modify:** `extension/manifest.json`

Add to `web_accessible_resources`:

```json
"web_accessible_resources": [
  {
    "resources": ["src/config/personalities.json"],
    "matches": ["<all_urls>"]
  }
]
```

---

## ✅ Acceptance Criteria

- [ ] `personalities.json` exists with at least 5 personality profiles
- [ ] Side panel shows personality selector grid
- [ ] Clicking a personality card selects it (visual feedback)
- [ ] Selection persists after closing/reopening side panel
- [ ] Each personality has: id, name, icon, description, systemPrompt

---

## 🧪 How to Test

1. Load the extension in Chrome (`chrome://extensions` → Load unpacked)
2. Go to any AI chat site (ChatGPT, Claude, etc.)
3. Click the Context Bridge extension icon to open side panel
4. Verify personality selector is visible
5. Click different personalities and verify selection changes
6. Close and reopen side panel - selection should persist

---

## 🔗 Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `extension/src/config/personalities.json` | CREATE | Personality definitions |
| `extension/src/sidepanel/index.html` | MODIFY | Add selector section |
| `extension/src/sidepanel/styles.css` | MODIFY | Add selector styles |
| `extension/src/sidepanel/index.js` | MODIFY | Add selector logic |
| `extension/manifest.json` | MODIFY | Add web_accessible_resources |

---

## ❓ Questions?

If you're stuck or have questions, reach out. Good luck! 🚀
