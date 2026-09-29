// js/protocol_engine.js
// Asha Vaani - Offline Malaria Protocol Engine
// Treatment rules are deterministic and based on the supplied
// Diagnosis & Treatment of Malaria (NVBDCP, 2013) document.
//
// IMPORTANT:
// - This engine does NOT diagnose malaria from symptoms.
// - This engine does NOT use an LLM to select treatment.
// - Severe/danger signs take priority over uncomplicated treatment.


// ============================================================
// 1. NORTH-EASTERN STATES
// ============================================================

const NORTH_EASTERN_STATES = [
  "Assam",
  "Arunachal Pradesh",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Tripura",
  "Sikkim"
];


// ============================================================
// 2. NORMALIZE STATE NAME
// ============================================================

function normalizeState(state) {
  if (!state) return "";

  return String(state)
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ")
    .replace(/&/g, "and");
}


// ============================================================
// 3. CHECK REGION
// ============================================================

function isNorthEasternState(state) {
  const normalized = normalizeState(state);

  return NORTH_EASTERN_STATES.some(
    s => normalizeState(s) === normalized
  );
}


// ============================================================
// 4. NORMALIZE RDT RESULT
// ============================================================

function normalizeTestResult(testResult) {
  if (!testResult) return "";

  const value = String(testResult).trim();

  // Existing values
  if (value === "Negative") return "Negative";
  if (value === "Pf_Positive") return "Pf_Positive";
  if (value === "Pv_Positive") return "Pv_Positive";
  if (value === "Mixed_Positive") return "Mixed_Positive";

  // Some possible future UI values
  if (value.toLowerCase().includes("mixed")) {
    return "Mixed_Positive";
  }

  if (
    value.toLowerCase().includes("falciparum") ||
    value.toLowerCase().includes("pf")
  ) {
    return "Pf_Positive";
  }

  if (
    value.toLowerCase().includes("vivax") ||
    value.toLowerCase().includes("pv")
  ) {
    return "Pv_Positive";
  }

  if (value.toLowerCase().includes("negative")) {
    return "Negative";
  }

  return value;
}


// ============================================================
// 5. NORMALIZE SYMPTOMS / DANGER SIGNS
// ============================================================

function normalizeArray(value) {
  if (!value) return [];

  if (Array.isArray(value)) {
    return value.map(item => String(item).trim()).filter(Boolean);
  }

  return [String(value).trim()].filter(Boolean);
}


// ============================================================
// 6. DANGER SIGN CHECK
// ============================================================

function hasDangerSigns(dangerSigns) {
  const signs = normalizeArray(dangerSigns);

  return signs.length > 0;
}


// ============================================================
// 7. MAIN PATIENT EVALUATION
// ============================================================

function evaluatePatient(
  age,
  gender,
  testResult,
  isPregnant,
  symptoms = [],
  dangerSigns = [],
  state = ""
) {

  let treatment = "";
  let action = "";

  const normalizedTest = normalizeTestResult(testResult);
  const normalizedSymptoms = normalizeArray(symptoms);
  const normalizedDangerSigns = normalizeArray(dangerSigns);

  // Convert age safely
  const numericAge = Number(age);


  // ==========================================================
  // CLINICAL GUARDRAILS
  // ==========================================================

  if (!Number.isFinite(numericAge)) {
    return {
      treatment: "INVALID INPUT",
      action: "Please enter a valid patient age."
    };
  }

  if (numericAge < 0 || numericAge > 120) {
    return {
      treatment: "INVALID INPUT",
      action: "Age must be between 0 and 120."
    };
  }


  // ----------------------------------------------------------
  // Male + pregnant
  // ----------------------------------------------------------

  if (gender === "Male" && isPregnant === "Yes") {
    return {
      treatment: "DATA ERROR",
      action:
        "A male patient cannot be marked as pregnant. Please fix the gender or pregnancy selection."
    };
  }


  // ----------------------------------------------------------
  // Current UI pregnancy validation
  // ----------------------------------------------------------

  if (numericAge < 15 && isPregnant === "Yes") {
    return {
      treatment: "DATA ERROR",
      action:
        "A patient under 15 years old cannot be marked as pregnant in this system. Please verify the age."
    };
  }


  // ==========================================================
  // DANGER SIGNS TAKE PRIORITY
  // ==========================================================

  if (hasDangerSigns(normalizedDangerSigns)) {

    return {
      treatment: "URGENT REFERRAL",
      action:
        "Danger sign(s) present. Refer immediately to the nearest PHC/health facility/hospital. Do not manage this as uncomplicated malaria.",
      region: state || "Not specified",
      testResult: normalizedTest,
      symptoms: normalizedSymptoms,
      dangerSigns: normalizedDangerSigns,
      urgent: true
    };
  }


  // ==========================================================
  // REGION
  // ==========================================================

  const region = isNorthEasternState(state)
    ? "North-Eastern States"
    : "Other States";


  // ==========================================================
  // 1. NEGATIVE RDT
  // ==========================================================

  if (normalizedTest === "Negative") {

    treatment = "No antimalarial treatment based on this negative RDT.";

    action =
      "Look for other causes of fever. If symptoms persist or worsen, seek medical evaluation.";

    return {
      treatment,
      action,
      region,
      testResult: normalizedTest,
      symptoms: normalizedSymptoms,
      dangerSigns: normalizedDangerSigns,
      urgent: false
    };
  }


  // ==========================================================
  // 2. PREGNANCY
  // ==========================================================

  if (isPregnant === "Yes") {

    return {
      treatment:
        "Pregnancy requires special malaria management. Do not give Primaquine.",
      action:
        "Refer the pregnant patient to the nearest PHC/health facility/hospital for appropriate treatment.",
      region,
      testResult: normalizedTest,
      symptoms: normalizedSymptoms,
      dangerSigns: normalizedDangerSigns,
      urgent: true
    };
  }


  // ==========================================================
  // 3. P. FALCIPARUM
  // ==========================================================

  if (normalizedTest === "Pf_Positive") {

    if (region === "North-Eastern States") {

      treatment =
        "ACT-AL for 3 days + Primaquine single dose on Day 2.";

      action =
        "Follow the age/weight-specific ACT-AL schedule. Refer if the patient develops danger signs or cannot tolerate oral treatment.";

    } else {

      treatment =
        "ACT-SP for 3 days + Primaquine single dose on Day 2.";

      action =
        "Follow the age/weight-specific ACT-SP schedule. Refer if the patient develops danger signs or cannot tolerate oral treatment.";
    }

    return {
      treatment,
      action,
      region,
      testResult: normalizedTest,
      symptoms: normalizedSymptoms,
      dangerSigns: normalizedDangerSigns,
      urgent: false
    };
  }


  // ==========================================================
  // 4. P. VIVAX
  // ==========================================================

  if (normalizedTest === "Pv_Positive") {

    treatment =
      "Chloroquine for 3 days + Primaquine for 14 days.";

    action =
      "Primaquine is contraindicated in pregnancy, infants and G6PD deficiency. Primaquine should be given under appropriate supervision.";

    return {
      treatment,
      action,
      region,
      testResult: normalizedTest,
      symptoms: normalizedSymptoms,
      dangerSigns: normalizedDangerSigns,
      urgent: false
    };
  }


  // ==========================================================
  // 5. MIXED INFECTION
  // ==========================================================

  if (normalizedTest === "Mixed_Positive") {

    if (region === "North-Eastern States") {

      treatment =
        "ACT-AL for 3 days + Primaquine for 14 days.";

    } else {

      treatment =
        "ACT-SP for 3 days + Primaquine for 14 days.";
    }

    action =
      "Follow the area-specific ACT schedule. Primaquine is contraindicated in pregnancy, infants and G6PD deficiency.";

    return {
      treatment,
      action,
      region,
      testResult: normalizedTest,
      symptoms: normalizedSymptoms,
      dangerSigns: normalizedDangerSigns,
      urgent: false
    };
  }


  // ==========================================================
  // 6. UNKNOWN / INVALID RDT
  // ==========================================================

  return {
    treatment: "RDT RESULT NOT RECOGNIZED",
    action:
      "Please select a valid RDT result: Negative, P. falciparum Positive, P. vivax Positive, or Mixed Positive.",
    region,
    testResult: normalizedTest,
    symptoms: normalizedSymptoms,
    dangerSigns: normalizedDangerSigns,
    urgent: false
  };
}