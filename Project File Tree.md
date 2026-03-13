# File Tree: instaAutoAI

```
├── 📁 docs
│   └── 📝 Architecture.md
├── 📁 instaAutoAI
│   ├── 📁 apps
│   │   ├── 📁 jobs
│   │   │   ├── 📁 management
│   │   │   │   ├── 📁 commands
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 purge_old_jobs.py
│   │   │   │   │   └── 🐍 retry_failed_jobs.py
│   │   │   │   └── 🐍 __init__.py
│   │   │   ├── 📁 tests
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   ├── 🐍 test_consumers.py
│   │   │   │   ├── 🐍 test_models.py
│   │   │   │   ├── 🐍 test_serializers.py
│   │   │   │   ├── 🐍 test_tasks.py
│   │   │   │   └── 🐍 test_views.py
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 admin.py
│   │   │   ├── 🐍 apps.py
│   │   │   ├── 🐍 consumers.py
│   │   │   ├── 🐍 exceptions.py
│   │   │   ├── 🐍 filters.py
│   │   │   ├── 🐍 models.py
│   │   │   ├── 🐍 pagination.py
│   │   │   ├── 🐍 permissions.py
│   │   │   ├── 🐍 routing.py
│   │   │   ├── 🐍 serializers.py
│   │   │   ├── 🐍 signals.py
│   │   │   ├── 🐍 tasks.py
│   │   │   ├── 🐍 urls.py
│   │   │   └── 🐍 views.py
│   │   ├── 📁 pipeline
│   │   │   ├── 📁 nodes
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   ├── 🐍 base.py
│   │   │   │   ├── 🐍 caption.py
│   │   │   │   ├── 🐍 export.py
│   │   │   │   ├── 🐍 hashtag.py
│   │   │   │   ├── 🐍 image_gen.py
│   │   │   │   ├── 🐍 strategy.py
│   │   │   │   ├── 🐍 video_gen.py
│   │   │   │   └── 🐍 visual_prompt.py
│   │   │   ├── 📁 tests
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   ├── 🐍 test_graph.py
│   │   │   │   ├── 🐍 test_nodes.py
│   │   │   │   ├── 🐍 test_runner.py
│   │   │   │   └── 🐍 test_vram_manager.py
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 apps.py
│   │   │   ├── 🐍 crew.py
│   │   │   ├── 🐍 exceptions.py
│   │   │   ├── 🐍 graph.py
│   │   │   ├── 🐍 health.py
│   │   │   ├── 🐍 llm_client.py
│   │   │   ├── 🐍 runner.py
│   │   │   ├── 🐍 state.py
│   │   │   └── 🐍 vram_manager.py
│   │   └── 📁 users
│   │       ├── 📁 tests
│   │       │   ├── 🐍 __init__.py
│   │       │   └── 🐍 test_views.py
│   │       ├── 🐍 __init__.py
│   │       ├── 🐍 admin.py
│   │       ├── 🐍 apps.py
│   │       ├── 🐍 models.py
│   │       ├── 🐍 serializers.py
│   │       ├── 🐍 urls.py
│   │       └── 🐍 views.py
│   ├── 📁 checkpoints
│   │   └── ⚙️ .gitkeep
│   ├── 📁 config
│   │   ├── 📁 settings
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 base.py
│   │   │   ├── 🐍 development.py
│   │   │   └── 🐍 production.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 asgi.py
│   │   ├── 🐍 celery.py
│   │   ├── 🐍 urls.py
│   │   └── 🐍 wsgi.py
│   ├── 📁 core
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 constants.py
│   │   ├── 🐍 middleware.py
│   │   ├── 🐍 mixins.py
│   │   ├── 🐍 storages.py
│   │   ├── 🐍 utils.py
│   │   └── 🐍 validators.py
│   ├── 📁 deploy
│   │   ├── ⚙️ .dockerignore
│   │   ├── 🐳 Dockerfile
│   │   ├── ⚙️ docker-compose.yml
│   │   ├── ⚙️ nginx.conf
│   │   └── ⚙️ supervisord.conf
│   ├── 📁 logs
│   │   └── ⚙️ .gitkeep
│   ├── 📁 media
│   │   └── 📁 jobs
│   │       └── ⚙️ .gitkeep
│   ├── 📁 scripts
│   │   ├── 🐍 seed_db.py
│   │   ├── 📄 start_services.bat
│   │   └── 📄 start_services.sh
│   ├── 📁 static
│   │   ├── 📁 css
│   │   │   └── 🎨 dashboard.css
│   │   ├── 📁 icons
│   │   └── 📁 js
│   │       └── 📄 dashboard.js
│   ├── 📁 templates
│   │   ├── 📁 errors
│   │   │   ├── 🌐 404.html
│   │   │   └── 🌐 500.html
│   │   ├── 🌐 base.html
│   │   └── 🌐 dashboard.html
│   ├── 📁 workflows
│   │   └── ⚙️ ltx_i2v_portrait.json
│   ├── ⚙️ .env.example
│   ├── ⚙️ .gitignore
│   ├── 📄 Makefile
│   ├── 🌐 instaAutoAI_gantt_7day.html
│   ├── 🐍 manage.py
│   ├── ⚙️ pyproject.toml
│   ├── 📄 requirements-dev.txt
│   └── 📄 requirements.txt
├── 📝 README.md
└── 📄 scaffold_instaAutoAI.sh
```
