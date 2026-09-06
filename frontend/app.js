/**
 * LAWDECODE Phase 4 - Frontend Application Logic
 * Handles all three agent outputs and the final legal analysis.
 */

document.addEventListener('DOMContentLoaded', () => {
  // ── UI Element References ──────────────────────────────────────────────
  const statusDot        = document.getElementById('status-dot');
  const statusText       = document.getElementById('status-text');

  const queryInput       = document.getElementById('query-input');
  const modelSelect      = document.getElementById('model-select');
  const btnAnalyze       = document.getElementById('btn-analyze');
  const btnAnalyzeText   = document.getElementById('btn-analyze-text');
  const btnClear         = document.getElementById('btn-clear');
  const btnCopy          = document.getElementById('btn-copy');
  const btnCopyAgent2    = document.getElementById('btn-copy-agent2');
  const btnCopyAgent3    = document.getElementById('btn-copy-agent3');

  // Agent 1 panel
  const responsePlaceholder = document.getElementById('response-placeholder');
  const responseLoading     = document.getElementById('response-loading');
  const responseErrorBox    = document.getElementById('response-error-box');
  const errorMessage        = document.getElementById('error-message');
  const responseContent     = document.getElementById('response-content');
  const responseModelBadge  = document.getElementById('response-model-badge');
  const terminalNote        = document.getElementById('terminal-note');

  // Agent 2 panel
  const agent2Panel         = document.getElementById('agent2-panel');
  const agent2StatusBadge   = document.getElementById('agent2-status-badge');
  const agent2Grid          = document.getElementById('agent2-grid');
  const agent2SummaryBlock  = document.getElementById('agent2-summary-block');
  const agent2Error         = document.getElementById('agent2-error');
  const agent2ErrorMsg      = document.getElementById('agent2-error-msg');
  const agent3Panel         = document.getElementById('agent3-panel');
  const agent3StatusBadge   = document.getElementById('agent3-status-badge');
  const agent3Error         = document.getElementById('agent3-error');
  const agent3ErrorMsg      = document.getElementById('agent3-error-msg');
  const toolsPanel          = document.getElementById('tools-panel');
  const toolsList           = document.getElementById('tools-list');
  const memoryPanel         = document.getElementById('memory-panel');
  const memoryList          = document.getElementById('memory-list');
  const workflowPanel       = document.getElementById('workflow-panel');
  const workflowList        = document.getElementById('workflow-list');

  // Agent status labels in architecture cards
  const agent1StatusLabel = document.getElementById('agent-1-status');
  const agent2StatusLabel = document.getElementById('agent-2-status');
  const agent3StatusLabel = document.getElementById('agent-3-status');

  // ── Initialise ─────────────────────────────────────────────────────────
  checkHealth();
  fetchAgents();

  // ── Preset chips ───────────────────────────────────────────────────────
  document.querySelectorAll('.chip-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const q = btn.getAttribute('data-query');
      if (q) { queryInput.value = q; queryInput.focus(); }
    });
  });

  // ── Clear ──────────────────────────────────────────────────────────────
  btnClear.addEventListener('click', () => {
    queryInput.value = '';
    queryInput.focus();
  });

  // ── Keyboard shortcut ──────────────────────────────────────────────────
  queryInput.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleAnalyze();
    }
  });

  // ── Analyze button ─────────────────────────────────────────────────────
  btnAnalyze.addEventListener('click', handleAnalyze);

  // ── Copy Agent 1 ───────────────────────────────────────────────────────
  btnCopy.addEventListener('click', async () => {
    const text = btnCopy.dataset.copyText;
    if (text) await copyToClipboard(btnCopy, text);
  });

  // ── Copy Agent 2 ───────────────────────────────────────────────────────
  btnCopyAgent2.addEventListener('click', async () => {
    const text = btnCopyAgent2.dataset.copyText;
    if (text) await copyToClipboard(btnCopyAgent2, text);
  });

  btnCopyAgent3.addEventListener('click', async () => {
    const text = btnCopyAgent3.dataset.copyText;
    if (text) await copyToClipboard(btnCopyAgent3, text);
  });

  // ── Health check ───────────────────────────────────────────────────────
  async function checkHealth() {
    try {
      const res  = await fetch('/api/health');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const provider = (data.provider || 'gemini').toUpperCase();
      configureModelOptions(provider.toLowerCase(), data.default_model);
      if (data.api_key_configured) {
        statusDot.className  = 'status-dot active';
        statusText.textContent = `${provider} API Ready — ${data.default_model}`;
        if (responseModelBadge) responseModelBadge.textContent = `Model: ${data.default_model}`;
      } else {
        statusDot.className  = 'status-dot warning pulse';
        statusText.textContent = `Action Required: Add ${provider}_API_KEY to .env`;
      }
    } catch (err) {
      statusDot.className  = 'status-dot';
      statusText.textContent = 'Backend Offline';
      console.warn('Could not contact LAWDECODE backend:', err);
    }
  }

  function configureModelOptions(provider, defaultModel) {
    if (!modelSelect) return;
    const models = provider === 'gemini'
      ? [
          ['gemini-3.5-flash-lite', 'Gemini 3.5 Flash Lite (Recommended)'],
          ['gemini-2.5-flash', 'Gemini 2.5 Flash'],
        ]
      : [
          ['gpt-4o-mini', 'GPT-4o mini (Recommended)'],
          ['gpt-4o', 'GPT-4o'],
        ];
    modelSelect.innerHTML = '';
    models.forEach(([value, label]) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      modelSelect.appendChild(option);
    });
    modelSelect.value = models.some(([value]) => value === defaultModel)
      ? defaultModel
      : models[0][0];
  }

  // ── Fetch agent statuses ───────────────────────────────────────────────
  async function fetchAgents() {
    try {
      const res = await fetch('/api/agents');
      if (!res.ok) return;
      const data = await res.json();
      if (data.agents && data.agents.length >= 3) {
        if (agent1StatusLabel) agent1StatusLabel.textContent = data.agents[0].status;
        if (agent2StatusLabel) agent2StatusLabel.textContent = data.agents[1].status;
        if (agent3StatusLabel) agent3StatusLabel.textContent = data.agents[2].status;
      }
    } catch (err) {
      console.warn('Could not fetch agent metadata:', err);
    }
  }

  // ── Main pipeline handler ──────────────────────────────────────────────
  async function handleAnalyze() {
    const query = queryInput.value.trim();
    if (!query) {
      queryInput.focus();
      queryInput.placeholder = 'Please enter a legal clause or query first...';
      return;
    }

    setLoading(true);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, model: modelSelect.value }),
      });

      // Safe JSON parse — never crash on non-JSON body
      let data;
      const raw = await res.text();
      try {
        data = JSON.parse(raw);
      } catch (_) {
        data = {
          success: false,
          error: `Server returned non-JSON response (HTTP ${res.status}). Please check the terminal for the Python traceback.`,
          api_key_configured: null,
        };
      }

      if (data.success && data.agent1) {
        showAgent1Success(data);
        showTools(data);
        showMemory(data);
        showWorkflow(data);
        showAgent2(data);
        showAgent3(data);
      } else {
        showError(data);
        showTools(data);
        showMemory(data);
        showWorkflow(data);
        // Still try to show Agent 2 if it ran
        if (data.agent2) showAgent2(data);
        if (data.agent3) showAgent3(data);
      }

      checkHealth();

    } catch (err) {
      showError({
        error: `Network error: ${err.message}. Verify the FastAPI backend is running on port 8000.`,
      });
    } finally {
      setLoading(false);
    }
  }

  // ── Loading state ──────────────────────────────────────────────────────
  function setLoading(isLoading) {
    if (isLoading) {
      btnAnalyze.disabled = true;
      btnAnalyzeText.textContent = 'Running Pipeline...';
      responsePlaceholder.style.display = 'none';
      responseErrorBox.style.display    = 'none';
      responseContent.style.display     = 'none';
      btnCopy.style.display             = 'none';
      terminalNote.style.display        = 'none';
      responseLoading.style.display     = 'flex';
      agent2Panel.style.display         = 'none';
      agent3Panel.style.display         = 'none';
      toolsPanel.style.display           = 'none';
      memoryPanel.style.display          = 'none';
      workflowPanel.style.display        = 'none';
    } else {
      btnAnalyze.disabled = false;
      btnAnalyzeText.textContent = 'Run Pipeline';
      responseLoading.style.display  = 'none';
    }
  }

  function showTools(data) {
    const tools = Array.isArray(data.tools) ? data.tools : ((data.agent1 || {}).tool_results || []);
    if (!toolsPanel || !toolsList || tools.length === 0) return;
    toolsList.innerHTML = '';
    tools.forEach(tool => {
      const item = document.createElement('article');
      item.className = `tool-result-item ${tool.success ? 'tool-success' : 'tool-error'}`;
      const result = typeof tool.result === 'object'
        ? JSON.stringify(tool.result, null, 2)
        : (tool.result || tool.error || 'No result');
      item.innerHTML = `<div class="tool-result-header"><strong>[TOOL USED] ${escapeHtml(tool.tool)}</strong><span>${tool.success ? 'Success' : 'Error'}</span></div><div class="tool-result-input">Input: ${escapeHtml(tool.input || '')}</div><pre>${escapeHtml(result)}</pre>`;
      toolsList.appendChild(item);
    });
    toolsPanel.style.display = 'block';
  }

  function showMemory(data) {
    const memory = data.memory || {};
    const interactions = Array.isArray(memory.retrieved) ? memory.retrieved : [];
    if (!memoryPanel || !memoryList) return;
    memoryList.innerHTML = '';
    const summary = document.createElement('p');
    summary.className = 'memory-summary';
    summary.textContent = `MEMORY: Retrieved ${memory.retrieved_count || 0} previous interactions${memory.saved ? ' | Current analysis saved locally' : ''}`;
    memoryList.appendChild(summary);
    interactions.forEach(interaction => {
      const item = document.createElement('article');
      item.className = 'memory-item';
      const conclusion = interaction.final_analysis && interaction.final_analysis.final_conclusion;
      item.innerHTML = `<div class="memory-item-meta">${escapeHtml(interaction.timestamp || 'Unknown time')} · relevance ${escapeHtml(interaction.relevance_score || '')}</div><strong>${escapeHtml(interaction.query || '')}</strong>${conclusion ? `<p>${escapeHtml(conclusion)}</p>` : ''}`;
      memoryList.appendChild(item);
    });
    memoryPanel.style.display = 'block';
  }

  function showWorkflow(data) {
    const events = Array.isArray(data.workflow_events) ? data.workflow_events : [];
    if (!workflowPanel || !workflowList || events.length === 0) return;
    workflowList.innerHTML = '';
    events.forEach((event, index) => {
      const item = document.createElement('li');
      item.className = event.startsWith('Tool ') ? 'workflow-tool-event' : 'workflow-event';
      item.innerHTML = `<span class="workflow-step">${String(index + 1).padStart(2, '0')}</span><span>${escapeHtml(event)}</span>`;
      workflowList.appendChild(item);
    });
    workflowPanel.style.display = 'block';
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[character]));
  }

  // ── Show Agent 1 success ───────────────────────────────────────────────
  function showAgent1Success(data) {
    responsePlaceholder.style.display = 'none';
    responseErrorBox.style.display    = 'none';
    responseLoading.style.display     = 'none';

    const a1 = data.agent1 || {};

    setText('res-main-issue', a1.main_issue);
    setText('res-summary',    a1.summary);
    populateList('res-key-facts',     a1.key_facts);
    populateList('res-parties',       a1.parties);
    populateList('res-legal-concepts',a1.legal_concepts);
    populateList('res-points-analysis', a1.points_for_further_analysis);

    responseContent.style.display = 'block';
    btnCopy.style.display         = 'inline-block';
    terminalNote.style.display    = 'flex';
    btnCopy.dataset.copyText      = JSON.stringify(a1, null, 2);

    if (data.model) responseModelBadge.textContent = `Model: ${data.model}`;
  }

  // ── Show Agent 2 panel ─────────────────────────────────────────────────
  function showAgent2(data) {
    const a2 = data.agent2 || {};
    agent2Panel.style.display = 'block';

    if (a2.status === 'Success') {
      agent2StatusBadge.textContent = 'Success';
      agent2StatusBadge.className   = 'agent2-status-badge success';
      agent2Grid.style.display      = 'grid';
      agent2SummaryBlock.style.display = 'block';
      agent2Error.style.display     = 'none';

      populateAgent2List('res2-legal-areas',    a2.legal_areas);
      populateAgent2List('res2-provisions',     a2.applicable_provisions);
      populateAgent2List('res2-principles',     a2.legal_principles);
      populateAgent2List('res2-considerations', a2.important_considerations);
      populateAgent2List('res2-ambiguities',    a2.ambiguities_and_conflicts);
      populateAgent2List('res2-points-agent3',  a2.points_for_agent3);

      setText('res2-summary', a2.research_summary);

      btnCopyAgent2.style.display    = 'inline-block';
      btnCopyAgent2.dataset.copyText = JSON.stringify(a2, null, 2);

    } else {
      // Skipped or Error
      agent2StatusBadge.textContent = a2.status || 'Skipped';
      agent2StatusBadge.className   = 'agent2-status-badge error';
      agent2Grid.style.display      = 'none';
      agent2SummaryBlock.style.display = 'none';
      agent2ErrorMsg.textContent    = a2.error || 'Agent 2 did not produce a result.';
      agent2Error.style.display     = 'block';
      btnCopyAgent2.style.display   = 'none';
    }
  }

  // ── Show Agent 3 and final analysis ────────────────────────────────────
  function showAgent3(data) {
    const a3 = data.agent3 || {};
    agent3Panel.style.display = 'block';

    if (a3.status === 'Success') {
      agent3StatusBadge.textContent = 'Success';
      agent3StatusBadge.className = 'agent2-status-badge success';
      agent3Error.style.display = 'none';

      setText('res3-key-issue', a3.key_legal_issue);
      setText('res3-interpretation', a3.legal_interpretation);
      setText('res3-risks', a3.risks_concerns);
      setText('res3-implications', a3.practical_implications);
      setText('res3-conclusion', a3.final_conclusion);
      setText('res3-disclaimer', a3.disclaimer);
      btnCopyAgent3.style.display = 'inline-block';
      btnCopyAgent3.dataset.copyText = JSON.stringify(a3, null, 2);
    } else {
      agent3StatusBadge.textContent = a3.status || 'Skipped';
      agent3StatusBadge.className = 'agent2-status-badge error';
      agent3ErrorMsg.textContent = a3.error || 'Agent 3 did not produce a result.';
      agent3Error.style.display = 'block';
      btnCopyAgent3.style.display = 'none';
    }
  }

  // ── Show error state ───────────────────────────────────────────────────
  function showError(data) {
    responsePlaceholder.style.display = 'none';
    responseContent.style.display     = 'none';
    responseLoading.style.display     = 'none';
    btnCopy.style.display             = 'none';

    const errText = data.error || 'Unknown error occurred.';

    if (data.api_key_configured === false || errText.includes('API_KEY')) {
      errorMessage.innerHTML = `
        <p><strong>AI API key is not configured.</strong></p>
        <p style="margin-top:6px;">Add the configured provider key to the project .env file:</p>
        <ol style="margin-left:18px;margin-top:6px;display:flex;flex-direction:column;gap:4px;">
          <li>Create a file named <code>.env</code> in the project root.</li>
          <li>Add your key:
            <pre style="margin-top:4px;padding:6px 10px;background:rgba(0,0,0,0.4);border-radius:6px;"><code>GEMINI_API_KEY=your_actual_gemini_key_here</code></pre>
          </li>
          <li>Resubmit — no restart needed.</li>
        </ol>`;
    } else {
      errorMessage.textContent = errText;
    }

    responseErrorBox.style.display = 'flex';
    terminalNote.style.display     = 'flex';
  }

  // ── Helpers ────────────────────────────────────────────────────────────
  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || 'None';
  }

  function populateList(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    const arr = Array.isArray(items) && items.length > 0 ? items : ['None identified'];
    arr.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      el.appendChild(li);
    });
  }

  function populateAgent2List(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    const arr = Array.isArray(items) && items.length > 0 ? items : ['None identified'];
    arr.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      el.appendChild(li);
    });
  }

  async function copyToClipboard(btn, text) {
    try {
      await navigator.clipboard.writeText(text);
      const orig = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = orig; }, 2000);
    } catch (err) {
      console.error('Clipboard copy failed:', err);
    }
  }
});
