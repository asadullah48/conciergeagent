// ConciergeAgent Interactive Controller & Bilingual Localization

let currentLang = 'en';
let selectedTier = 'ULTRA_HNW';

const TRANSLATIONS = {
  en: {
    badgeTitle: "Five-Star Hospitality AI",
    statusLive: "Concierge Active (:8005)",
    heroTitle: "White-Glove Hyperpersonalization & Bespoke AI Advisory",
    heroSubtitle: "Empowering banking, private wealth, insurance, and luxury retail with tier-adapted financial advisory, instant dispute resolution, and five-star customer experience governance.",
    metric1Label: "Predicted CSAT",
    metric1Sub: "Hospitality & Empathy Score",
    metric2Label: "Ultra-VIP SLA",
    metric2Sub: "Dedicated Family Office Lead",
    metric3Label: "Instant Auto-Credit",
    metric3Sub: "Zero-Liability VIP Protection",
    metric4Label: "Private Yield Alpha",
    metric4Sub: "Tax-Loss Harvested Portfolios",
    studioTitle: "Hyperpersonalized Concierge Studio",
    studioDesc: "Switch wealth tiers, select bespoke scenarios, and watch real-time empathetic tone modulation, advisory allocation, and VIP privilege gifting.",
    lblWealthTier: "Customer Wealth Tier",
    lblPresets: "Bespoke Touchpoint Scenarios:",
    lblQuery: "Customer Query / Request",
    btnEngage: "🛎️ Engage Concierge Service",
    titleConciergeOutput: "Concierge Response & Five-Star Review",
    lblAllocationTitle: "Bespoke Asset Allocation Model:"
  },
  ar: {
    badgeTitle: "ذكاء اصطناعي للضيافة الفاخرة 5 نجوم",
    statusLive: "خدمة الكونسيرج نشطة (:8005)",
    heroTitle: "خدمة راقية فائقة التخصيص واستشارات مالية استباقية",
    heroSubtitle: "تمكين القطاع المصرفي وإدارة الثروات والتأمين والتجزئة الفاخرة من تقديم استشارات مخصصة وحل فوري للنزاعات بأعلى معايير الضيافة.",
    metric1Label: "معدل الرضا المتوقع",
    metric1Sub: "مؤشر التعاطف والضيافة الراقية",
    metric2Label: "اتفاقية مستوى الخدمة لكبار العملاء",
    metric2Sub: "مستشار مخصص لمكاتب العائلات",
    metric3Label: "الائتمان الفوري للنزاعات",
    metric3Sub: "حماية فورية منعدمة المسؤولية",
    metric4Label: "العائد الاستثماري الإضافي",
    metric4Sub: "محافظ استثمارية محسنة ضريبياً",
    studioTitle: "استوديو الكونسيرج الرقمي فائق التخصيص",
    studioDesc: "تنقل بين شرائح الثروة، واختر السيناريوهات الحية وشاهد الضبط الفوري لنبرة الحديث وتوزيع الأصول وهدايا الولاء.",
    lblWealthTier: "شريحة ثروة العميل",
    lblPresets: "سيناريوهات التواصل الفاخرة:",
    lblQuery: "استفسار أو طلب العميل",
    btnEngage: "🛎️ تفعيل خدمة الكونسيرج الرقمي",
    titleConciergeOutput: "رد الكونسيرج وتقييم تجربة العميل 5 نجوم",
    lblAllocationTitle: "نموذج التوزيع الاستثماري المخصص للأصول:"
  }
};

const PROFILES = {
  ULTRA_HNW: {
    customer_id: "CUST-ULTRA-01",
    name: "Lord Sterling",
    wealth_tier: "ULTRA_HNW",
    primary_domain: "BANKING",
    assets_under_management_usd: 15000000.0,
    lifetime_value_score: 98.5,
    loyalty_points: 450000,
    preferred_tone: "Concierge Formal",
    relationship_tenure_years: 12,
    badgeText: "ULTRA_HNW ($15M AUM)",
    officer: "Executive Family Office Lead",
    sla: "30 Seconds",
    credit: "$50,000.00"
  },
  PRIVATE_CLIENT: {
    customer_id: "CUST-PRIV-02",
    name: "Alexander Wright",
    wealth_tier: "PRIVATE_CLIENT",
    primary_domain: "BANKING",
    assets_under_management_usd: 3500000.0,
    lifetime_value_score: 92.0,
    loyalty_points: 120000,
    preferred_tone: "Executive Formal",
    relationship_tenure_years: 6,
    badgeText: "PRIVATE_CLIENT ($3.5M AUM)",
    officer: "Senior Private Banker",
    sla: "60 Seconds",
    credit: "$10,000.00"
  },
  PREMIER: {
    customer_id: "CUST-PREM-03",
    name: "Dr. Evelyn Reed",
    wealth_tier: "PREMIER",
    primary_domain: "BANKING",
    assets_under_management_usd: 350000.0,
    lifetime_value_score: 84.0,
    loyalty_points: 45000,
    preferred_tone: "Professional Warm",
    relationship_tenure_years: 3,
    badgeText: "PREMIER ($350k AUM)",
    officer: "Premier Relationship Manager",
    sla: "120 Seconds",
    credit: "$2,500.00"
  },
  RETAIL: {
    customer_id: "CUST-RET-04",
    name: "Sarah Jenkins",
    wealth_tier: "RETAIL",
    primary_domain: "BANKING",
    assets_under_management_usd: 25000.0,
    lifetime_value_score: 72.0,
    loyalty_points: 5000,
    preferred_tone: "Friendly Helpful",
    relationship_tenure_years: 1,
    badgeText: "RETAIL ($25k AUM)",
    officer: "Digital Concierge Assistant",
    sla: "300 Seconds",
    credit: "$500.00"
  }
};

const SCENARIOS = [
  {
    name: "💎 Private Equity Co-Investment Allocation",
    intent: "ADVISORY",
    query: "Please structure a private wealth asset allocation focusing on tax efficiency and pre-IPO secondary opportunities for my trust."
  },
  {
    name: "💳 Unauthorized $8,500 Platinum Card Charge",
    intent: "SUPPORT",
    query: "I noticed an unrecognized luxury hotel charge of $8,500 on my card while in London. Please dispute and secure my account."
  },
  {
    name: "🛡️ Expedited VIP Marine & Yacht Insurance Claim",
    intent: "SUPPORT",
    query: "Our Mediterranean yacht experienced electrical storm damage. Please fast-track our comprehensive insurance claim."
  },
  {
    name: "📈 Proactive Portfolio Yield Rebalancing",
    intent: "ADVISORY",
    query: "How can we optimize our fixed income yield and execute tax-loss harvesting before year-end?"
  }
];

function init() {
  renderPresets();
  updatePersonaCard();
  loadScenario(0);
}

function toggleLanguage() {
  currentLang = currentLang === 'en' ? 'ar' : 'en';
  document.documentElement.lang = currentLang;
  document.documentElement.dir = currentLang === 'ar' ? 'rtl' : 'ltr';
  document.getElementById('langLabel').innerText = currentLang === 'en' ? 'العربية' : 'English';

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (TRANSLATIONS[currentLang][key]) {
      el.innerText = TRANSLATIONS[currentLang][key];
    }
  });
}

function selectTier(tier) {
  selectedTier = tier;
  document.querySelectorAll('.tier-btn').forEach(btn => {
    btn.classList.toggle('active', btn.innerText.includes(tier.replace('_', ' ')));
  });
  updatePersonaCard();
}

function updatePersonaCard() {
  const p = PROFILES[selectedTier];
  document.getElementById('personaName').innerText = p.name;
  document.getElementById('personaTierBadge').innerText = p.badgeText;
  document.getElementById('personaLtv').innerText = `LTV: ${p.lifetime_value_score}`;
  document.getElementById('personaOfficer').innerText = p.officer;
  document.getElementById('personaSla').innerText = p.sla;
  document.getElementById('personaCredit').innerText = p.credit;
}

function renderPresets() {
  const container = document.getElementById('scenarioButtons');
  container.innerHTML = '';
  SCENARIOS.forEach((sc, idx) => {
    const btn = document.createElement('button');
    btn.className = 'preset-btn';
    btn.innerText = sc.name;
    btn.onclick = () => loadScenario(idx);
    container.appendChild(btn);
  });
}

function loadScenario(idx) {
  const sc = SCENARIOS[idx];
  document.getElementById('queryInput').value = sc.query;
}

async function runConcierge() {
  const btn = document.getElementById('conciergeBtn');
  const query = document.getElementById('queryInput').value.trim();
  const profile = PROFILES[selectedTier];

  btn.disabled = true;
  btn.innerText = "Consulting Concierge Agents...";

  try {
    const res = await fetch('/api/v1/concierge/interact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interaction_id: `INT-${Date.now()}`,
        customer_profile: profile,
        user_query: query,
        intent_category: query.toLowerCase().includes('dispute') || query.toLowerCase().includes('claim') ? 'SUPPORT' : 'ADVISORY',
        raw_sentiment_score: query.toLowerCase().includes('dispute') ? -0.4 : 0.85
      })
    });

    const data = await res.json();

    // Render dialog
    document.getElementById('conciergeResponseText').innerText = data.concierge_response_text;
    
    // Render badge
    const badge = document.getElementById('sentimentBadge');
    badge.innerText = `⭐ ${data.experience_review.hospitality_rating}.0 Stars (${data.experience_review.sentiment_grade})`;
    badge.className = data.experience_review.executive_escalation_required ? 'badge badge-danger' : 'badge badge-success';

    // Render VIP perk card
    const perkCard = document.getElementById('vipPerkCard');
    if (data.experience_review.loyalty_perk_awarded) {
      perkCard.style.display = 'flex';
      document.getElementById('perkText').innerText = data.experience_review.loyalty_perk_awarded;
    } else {
      perkCard.style.display = 'none';
    }

    // Render Allocation if advisory
    const allocCard = document.getElementById('allocationCard');
    const allocGrid = document.getElementById('allocationGrid');
    if (data.advisory_recommendation && data.advisory_recommendation.portfolio_allocation) {
      allocCard.style.display = 'flex';
      allocGrid.innerHTML = '';
      for (const [k, v] of Object.entries(data.advisory_recommendation.portfolio_allocation)) {
        const row = document.createElement('div');
        row.innerHTML = `
          <div class="alloc-row"><span>${k}</span><span>${(v * 100).toFixed(0)}%</span></div>
          <div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:${v * 100}%;"></div></div>
        `;
        allocGrid.appendChild(row);
      }
    } else {
      allocCard.style.display = 'none';
    }

  } catch (err) {
    document.getElementById('conciergeResponseText').innerText = `Error connecting to ConciergeAgent Gateway: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.innerText = TRANSLATIONS[currentLang].btnEngage;
  }
}

window.addEventListener('DOMContentLoaded', init);
