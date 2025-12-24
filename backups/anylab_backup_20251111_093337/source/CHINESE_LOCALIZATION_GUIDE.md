# Chinese Localization Guide (中文本地化指南)

**Date Created:** 2025-01-XX  
**Status:** Planning Phase - Documentation Only (No Code Changes)

## Overview (概述)

This document outlines the comprehensive approach for implementing Chinese (Simplified) localization for the AnyLab platform. All text strings, UI elements, API responses, and user-facing content will be translated to Chinese.

本文档概述了为 AnyLab 平台实现中文（简体）本地化的全面方法。所有文本字符串、UI 元素、API 响应和面向用户的内容都将翻译成中文。

## Table of Contents (目录)

1. [Architecture Overview](#architecture-overview)
2. [Frontend Localization](#frontend-localization)
3. [Backend Localization](#backend-localization)
4. [API Response Localization](#api-response-localization)
5. [Database Content](#database-content)
6. [AI Response Localization](#ai-response-localization)
7. [Implementation Phases](#implementation-phases)
8. [File Structure](#file-structure)
9. [Testing Strategy](#testing-strategy)
10. [Estimated Effort](#estimated-effort)

---

## Architecture Overview (架构概述)

### Current State (当前状态)

- **Frontend**: React + TypeScript with hardcoded English strings
- **Backend**: Django with `USE_I18N = True` but `LANGUAGE_CODE = 'en-us'`
- **No i18n libraries**: Neither frontend nor backend have internationalization setup
- **Text strings**: All hardcoded in English throughout the codebase

### Target State (目标状态)

- **Frontend**: React with `react-i18next` for UI translations
- **Backend**: Django with full i18n support using `gettext`
- **Language Support**: Simplified Chinese (zh-CN) as primary, English (en-US) as fallback
- **User Preference**: Language stored in user profile and localStorage

---

## Frontend Localization (前端本地化)

### Recommended Solution: react-i18next

**Why react-i18next?**
- ✅ Excellent React and TypeScript support
- ✅ Lazy loading of translation files
- ✅ Active maintenance and large community
- ✅ Type-safe translations with TypeScript
- ✅ Browser language detection
- ✅ Namespace support for organizing translations

### Implementation Steps (实施步骤)

#### 1. Install Dependencies
```bash
cd frontend
npm install react-i18next i18next i18next-browser-languagedetector
npm install --save-dev @types/react-i18next  # If using TypeScript
```

#### 2. Create Translation Files Structure

```
frontend/src/
├── locales/
│   ├── zh-CN/
│   │   ├── common.json          # 通用文本 (通用按钮、标签等)
│   │   ├── sidebar.json         # 侧边栏导航
│   │   ├── dashboard.json       # 仪表板
│   │   ├── ai.json              # AI助手相关
│   │   ├── auth.json            # 认证页面
│   │   ├── admin.json           # 管理界面
│   │   ├── forum.json           # 论坛
│   │   ├── documents.json       # 文档管理
│   │   ├── errors.json          # 错误消息
│   │   └── validation.json      # 表单验证
│   └── en-US/
│       └── (same structure for English fallback)
├── i18n/
│   └── config.ts                # i18next configuration
└── components/
    └── ... (components using t() function)
```

#### 3. Translation File Examples

**common.json (zh-CN)**
```json
{
  "buttons": {
    "save": "保存",
    "cancel": "取消",
    "delete": "删除",
    "edit": "编辑",
    "search": "搜索",
    "upload": "上传",
    "download": "下载",
    "submit": "提交",
    "reset": "重置"
  },
  "labels": {
    "username": "用户名",
    "password": "密码",
    "email": "电子邮件",
    "loading": "加载中...",
    "noData": "暂无数据"
  }
}
```

**sidebar.json (zh-CN)**
```json
{
  "dashboard": "仪表板",
  "knowledgeLibrary": "知识库",
  "libraryManager": "库管理器",
  "productManuals": "产品手册",
  "technicalSpecs": "技术规格",
  "communitySolutions": "社区解决方案",
  "documentViewer": "文档查看器",
  "aiAssistant": "AI助手",
  "freeAiChat": "免费AI聊天",
  "basicRag": "基础RAG",
  "advancedRag": "高级RAG",
  "comprehensiveRag": "综合RAG",
  "graphRag": "图谱RAG",
  "troubleshootingAi": "故障排除AI",
  "forum": "论坛",
  "administration": "管理",
  "usersRoles": "用户和角色",
  "licenses": "许可证",
  "systemSettings": "系统设置"
}
```

#### 4. i18next Configuration

**i18n/config.ts**
```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import commonZh from '../locales/zh-CN/common.json';
import commonEn from '../locales/en-US/common.json';
import sidebarZh from '../locales/zh-CN/sidebar.json';
import sidebarEn from '../locales/en-US/sidebar.json';
// ... import other namespaces

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      'zh-CN': {
        common: commonZh,
        sidebar: sidebarZh,
        // ... other namespaces
      },
      'en-US': {
        common: commonEn,
        sidebar: sidebarEn,
        // ... other namespaces
      },
    },
    fallbackLng: 'en-US',
    defaultNS: 'common',
    ns: ['common', 'sidebar', 'dashboard', 'ai', 'auth', 'admin'],
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'anylab_language',
    },
  });

export default i18n;
```

#### 5. Component Usage Example

**Before:**
```tsx
<h1>Dashboard</h1>
<button>Save</button>
```

**After:**
```tsx
import { useTranslation } from 'react-i18next';

const Dashboard = () => {
  const { t } = useTranslation(['dashboard', 'common']);
  
  return (
    <>
      <h1>{t('dashboard.title')}</h1>
      <button>{t('common:buttons.save')}</button>
    </>
  );
};
```

#### 6. Language Switcher Component

Create a language switcher in TopBar or Settings:

```tsx
import { useTranslation } from 'react-i18next';

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();
  
  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('anylab_language', lng);
  };
  
  return (
    <select 
      value={i18n.language} 
      onChange={(e) => changeLanguage(e.target.value)}
    >
      <option value="zh-CN">简体中文</option>
      <option value="en-US">English</option>
    </select>
  );
};
```

### Files to Update (需要更新的文件)

**High Priority (高优先级):**
- `frontend/src/components/Layout/Sidebar.tsx` - Navigation menu
- `frontend/src/components/Auth/Login.tsx` - Login page
- `frontend/src/components/Dashboard/Dashboard.tsx` - Dashboard
- `frontend/src/components/Layout/TopBar.tsx` - Top navigation
- `frontend/src/components/Home/HomePage.tsx` - Home page

**Medium Priority (中优先级):**
- All AI components (`frontend/src/components/AI/*.tsx`)
- Administration components (`frontend/src/components/Administration/*.tsx`)
- Forum components (`frontend/src/components/Forum/*.tsx`)

**Low Priority (低优先级):**
- UI components (`frontend/src/components/ui/*.tsx`)
- Utility components

---

## Backend Localization (后端本地化)

### Django i18n Setup

#### 1. Update settings.py

```python
# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'  # Simplified Chinese
# Alternative: 'zh-hant' for Traditional Chinese

LANGUAGES = [
    ('zh-hans', '简体中文'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

USE_I18N = True
USE_L10N = True  # Enable localization of numbers, dates, etc.
USE_TZ = True

TIME_ZONE = 'Asia/Shanghai'  # Or your preferred timezone
```

#### 2. Update MIDDLEWARE

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Add this after SessionMiddleware
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware
]
```

#### 3. Mark Strings for Translation

**In views.py:**
```python
from django.utils.translation import gettext as _

def create_user(request):
    # ...
    return JsonResponse({
        'message': _('User created successfully'),
        'status': 'success'
    })
```

**In models.py:**
```python
from django.utils.translation import gettext_lazy as _

class Document(models.Model):
    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    
    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
```

**In forms.py:**
```python
from django.utils.translation import gettext_lazy as _

class LoginForm(forms.Form):
    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
```

#### 4. Generate Translation Files

```bash
cd backend
python manage.py makemessages -l zh_Hans
python manage.py makemessages -l zh_Hant  # If Traditional Chinese needed
```

This creates `locale/zh_Hans/LC_MESSAGES/django.po`

#### 5. Translate in .po Files

Edit `locale/zh_Hans/LC_MESSAGES/django.po`:

```po
#: users/views.py:45
msgid "User created successfully"
msgstr "用户创建成功"

#: users/forms.py:12
msgid "Username"
msgstr "用户名"
```

#### 6. Compile Translations

```bash
python manage.py compilemessages
```

This creates `django.mo` files that Django uses at runtime.

### Files to Update (需要更新的文件)

**High Priority:**
- `backend/users/views.py` - User management views
- `backend/users/forms.py` - User forms
- `backend/ai_assistant/views.py` - AI assistant API responses
- `backend/forum/views.py` - Forum views

**Medium Priority:**
- `backend/users/models.py` - Model verbose names
- `backend/ai_assistant/models.py` - Model verbose names
- Error messages in all views

---

## API Response Localization (API响应本地化)

### Approach Options

#### Option 1: Accept-Language Header (Recommended)

**Frontend:**
```typescript
// In api.ts
const apiClient = axios.create({
  headers: {
    'Accept-Language': localStorage.getItem('anylab_language') || 'zh-CN',
  },
});
```

**Backend:**
```python
# Django automatically handles Accept-Language header
# when LocaleMiddleware is enabled
from django.utils.translation import activate, get_language

def api_view(request):
    # Language is automatically set by middleware
    language = get_language()  # Returns 'zh-hans' or 'en'
    return JsonResponse({
        'message': _('Operation successful'),
        'data': data
    })
```

#### Option 2: Query Parameter

```python
def api_view(request):
    lang = request.GET.get('lang', 'zh-hans')
    activate(lang)
    return JsonResponse({
        'message': _('Operation successful'),
    })
```

#### Option 3: User Profile Setting

```python
# Store language preference in user profile
class User(AbstractUser):
    language = models.CharField(
        max_length=10,
        choices=LANGUAGES,
        default='zh-hans'
    )

# In views
def api_view(request):
    if request.user.is_authenticated:
        activate(request.user.language)
    return JsonResponse({...})
```

**Recommendation:** Use Option 1 (Accept-Language header) + Option 3 (user preference) as fallback.

---

## Database Content (数据库内容)

### User-Generated Content Translation

For content created by users (forum posts, document titles, etc.), there are several approaches:

#### Option A: Separate Language Fields

```python
class Document(models.Model):
    title_en = models.CharField(max_length=200)
    title_zh = models.CharField(max_length=200)
    description_en = models.TextField()
    description_zh = models.TextField()
```

#### Option B: Translation Table

```python
class DocumentTranslation(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    language = models.CharField(max_length=10)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    class Meta:
        unique_together = [['document', 'language']]
```

#### Option C: JSON Field

```python
class Document(models.Model):
    title = models.JSONField(default=dict)  # {'en': '...', 'zh': '...'}
    description = models.JSONField(default=dict)
```

**Recommendation:** For initial implementation, keep original language and add translation fields later if needed. Use AI translation API for dynamic translation if required.

---

## AI Response Localization (AI响应本地化)

### Qwen 2.5-7B Chinese Support

Qwen 2.5-7B has excellent Chinese language support. To ensure responses are in Chinese:

#### 1. Update System Prompts

```python
# In ai_assistant/views.py or services
SYSTEM_PROMPT_ZH = """你是一个专业的实验室知识助手。请用简体中文回答所有问题。
提供准确、详细、专业的回答。"""

SYSTEM_PROMPT_EN = """You are a professional lab knowledge assistant. 
Answer all questions in English. Provide accurate, detailed, professional answers."""

def get_system_prompt(language='zh'):
    if language == 'zh' or language.startswith('zh'):
        return SYSTEM_PROMPT_ZH
    return SYSTEM_PROMPT_EN
```

#### 2. Pass Language to AI Service

```python
def chat_endpoint(request):
    user_language = request.headers.get('Accept-Language', 'zh-CN')
    lang_code = 'zh' if 'zh' in user_language.lower() else 'en'
    
    system_prompt = get_system_prompt(lang_code)
    
    response = ollama_client.chat(
        model='qwen2.5:latest',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query}
        ]
    )
    
    return JsonResponse({'response': response})
```

#### 3. Update RAG Prompts

Ensure RAG prompts also include language instructions:

```python
RAG_PROMPT_ZH = """基于以下文档内容，用简体中文回答问题。
如果文档中没有相关信息，请说明。"""

RAG_PROMPT_EN = """Answer the question in English based on the following document content.
If the information is not in the documents, please state so."""
```

---

## Implementation Phases (实施阶段)

### Phase 1: Foundation (基础阶段) - Week 1

**Frontend:**
- [ ] Install react-i18next dependencies
- [ ] Create i18n configuration
- [ ] Create translation file structure
- [ ] Translate common.json (buttons, labels, errors)
- [ ] Translate sidebar.json
- [ ] Add language switcher component
- [ ] Update Sidebar.tsx to use translations

**Backend:**
- [ ] Update settings.py with i18n configuration
- [ ] Add LocaleMiddleware
- [ ] Mark strings in users/views.py
- [ ] Generate and translate django.po files
- [ ] Compile messages

**Estimated Time:** 16-20 hours

### Phase 2: Core UI (核心UI) - Week 2

**Frontend:**
- [ ] Translate dashboard.json and update Dashboard.tsx
- [ ] Translate auth.json and update Login.tsx
- [ ] Translate all AI component files
- [ ] Translate admin.json and administration components
- [ ] Update TopBar with language switcher

**Backend:**
- [ ] Translate API error messages
- [ ] Translate ai_assistant/views.py responses
- [ ] Update model verbose names

**Estimated Time:** 20-24 hours

### Phase 3: Advanced Features (高级功能) - Week 3

**Frontend:**
- [ ] Translate forum components
- [ ] Translate document management components
- [ ] Translate validation messages
- [ ] Test all components with Chinese text

**Backend:**
- [ ] Translate forum views
- [ ] Update AI system prompts for Chinese
- [ ] Test API responses in Chinese

**Estimated Time:** 16-20 hours

### Phase 4: Polish & Testing (完善和测试) - Week 4

- [ ] UI layout testing with Chinese text
- [ ] Font rendering verification
- [ ] Date/time format localization
- [ ] Number format localization
- [ ] Performance testing
- [ ] User acceptance testing
- [ ] Documentation updates

**Estimated Time:** 12-16 hours

**Total Estimated Time:** 64-80 hours (8-10 working days)

---

## File Structure (文件结构)

### Final Structure

```
AnyLab103/
├── frontend/
│   ├── src/
│   │   ├── locales/
│   │   │   ├── zh-CN/
│   │   │   │   ├── common.json
│   │   │   │   ├── sidebar.json
│   │   │   │   ├── dashboard.json
│   │   │   │   ├── ai.json
│   │   │   │   ├── auth.json
│   │   │   │   ├── admin.json
│   │   │   │   ├── forum.json
│   │   │   │   ├── documents.json
│   │   │   │   ├── errors.json
│   │   │   │   └── validation.json
│   │   │   └── en-US/
│   │   │       └── (same structure)
│   │   ├── i18n/
│   │   │   └── config.ts
│   │   └── components/
│   │       └── ... (updated components)
│   └── package.json (updated dependencies)
│
├── backend/
│   ├── locale/
│   │   ├── zh_Hans/
│   │   │   └── LC_MESSAGES/
│   │   │       ├── django.po
│   │   │       └── django.mo
│   │   └── en/
│   │       └── LC_MESSAGES/
│   │           ├── django.po
│   │           └── django.mo
│   ├── anylab/
│   │   └── settings.py (updated i18n config)
│   └── users/
│       └── models.py (add language field)
│
└── docs/
    └── CHINESE_LOCALIZATION_GUIDE.md (this file)
```

---

## Testing Strategy (测试策略)

### 1. Unit Testing

- Test translation loading
- Test language switching
- Test fallback to English

### 2. Integration Testing

- Test API responses with different Accept-Language headers
- Test user preference persistence
- Test AI responses in Chinese

### 3. UI Testing

- Test text overflow with Chinese characters
- Test font rendering
- Test layout with longer/shorter Chinese text
- Test date/time/number formatting

### 4. User Acceptance Testing

- Native Chinese speakers review translations
- Test all user flows in Chinese
- Verify technical terms are correctly translated

### Test Checklist

- [ ] All UI text displays in Chinese
- [ ] Language switcher works correctly
- [ ] API error messages are in Chinese
- [ ] Form validation messages are in Chinese
- [ ] AI responses are in Chinese
- [ ] Date/time formats are localized
- [ ] Number formats are localized
- [ ] No text overflow issues
- [ ] Fonts render Chinese characters correctly
- [ ] User preference persists across sessions

---

## Considerations (注意事项)

### Text Length

- Chinese text can be shorter or longer than English
- Test UI layouts with both short and long Chinese strings
- Ensure buttons, cards, and modals accommodate text length variations

### Font Support

- Ensure fonts support Chinese characters
- Consider using system fonts or web fonts with Chinese support
- Test font rendering on different browsers and OS

### Date/Time Formats

- Use Chinese locale formats: `2025年1月15日` instead of `January 15, 2025`
- Configure TIME_ZONE in settings.py
- Use Django's date formatting: `{{ date|date:"Y年m月d日" }}`

### Number Formats

- Chinese number formats may differ
- Use Django's number formatting for consistency

### Technical Terms

- Some technical terms may remain in English (e.g., "RAG", "API", "PDF")
- Create a glossary of technical terms
- Consider adding tooltips for technical terms

### RTL Support

- Not needed for Chinese (Chinese is LTR like English)
- But good to keep in mind for future languages

---

## Estimated Effort (工作量估算)

### Breakdown by Component

| Component | Estimated Hours |
|-----------|----------------|
| Frontend i18n setup | 4-6 hours |
| Translation file creation | 16-20 hours |
| Component updates (Frontend) | 20-24 hours |
| Backend i18n setup | 3-4 hours |
| Backend string marking | 8-10 hours |
| Backend translation | 6-8 hours |
| API response localization | 4-6 hours |
| AI prompt updates | 2-3 hours |
| Testing & refinement | 12-16 hours |
| Documentation | 4-6 hours |
| **Total** | **79-103 hours** |

### Timeline

- **Fast Track (1 developer, full-time):** 2-3 weeks
- **Normal Pace (1 developer, part-time):** 4-6 weeks
- **With Review Cycles:** 6-8 weeks

---

## Next Steps (下一步)

1. **Review this documentation** with the team
2. **Decide on implementation approach** (phased vs. all-at-once)
3. **Set up translation workflow** (who will translate, review process)
4. **Create translation files** with initial translations
5. **Begin Phase 1 implementation**
6. **Set up testing environment** for Chinese language
7. **Schedule review sessions** with native Chinese speakers

---

## Resources (资源)

### Translation Tools

- **Google Translate API** - For initial machine translation (needs human review)
- **DeepL** - High-quality machine translation
- **Translation Memory** - Reuse translations across the project

### Documentation

- [react-i18next Documentation](https://react.i18next.com/)
- [Django i18n Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [i18next Documentation](https://www.i18next.com/)

### Chinese Language Resources

- [Simplified vs Traditional Chinese](https://en.wikipedia.org/wiki/Simplified_Chinese_characters)
- [Chinese Typography Guidelines](https://www.smashingmagazine.com/2012/04/chinese-web-typography-designing-for-readability/)

---

## Support (支持)

For questions or issues during implementation:
- Review this documentation
- Check the implementation phases
- Consult with native Chinese speakers for translation accuracy
- Test thoroughly before deployment

---

**Last Updated:** 2025-01-XX  
**Status:** Planning Phase - Ready for Implementation  
**Version:** 1.0.0

