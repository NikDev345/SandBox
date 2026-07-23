from nicegui import ui, app
from app.api.auth import router as auth_router


app.add_static_files(
    '/assets',
    'app/ui/assets'
)
app.include_router(auth_router)

@ui.page('/')
def home():
    ui.label('Hello SandBox')

ui.add_head_html("""
<link rel="stylesheet" href="/assets/css/auth.css">

<script type="module" src="/assets/js/appearance.js"></script>
""", shared=True)


import app.main

import app.ui.pages.login
import app.ui.pages.signup
import app.ui.pages.dashboard
import app.ui.pages.profile
import app.ui.pages.tool_page
import app.ui.pages.forgot_password
import app.ui.pages.reset_password
import app.ui.pages.text_summarizer
import app.ui.pages.json_fixer
import app.ui.pages.image_text_extractor
import app.ui.pages.eli5
import app.ui.pages.ss_explain
import app.ui.pages.sql_generator
import app.ui.pages.table_extractor
import app.ui.pages.notes_cleaner
import app.ui.pages.mock_api
import app.ui.pages.chart_explainer
import app.ui.pages.chart_explainer
import app.ui.pages.email_rewriter
import app.ui.pages.blog_outline_generator
import app.ui.pages.pro_cons
import app.ui.pages.quiz_generator
import app.ui.pages.flashcard_generator
import app.ui.pages.youtube_summarizer
import app.ui.pages.regex
# ui.run(
#     title='SandBox',
#     dark=True,
#     reload=True
# )
