// js/protocol_engine.js

function evaluatePatient(age, testResult, isPregnant) {
  let treatment = "";
  let action = "";

  // --- CLINICAL GUARDRAILS (VALIDATION) ---
  if (age < 0 || age > 120) {
    return { treatment: "INVALID INPUT", action: "Age must be between 0 and 120." };
  }
  
  if (age < 10 && isPregnant === "Yes") {
    return { 
      treatment: "DATA ERROR", 
      action: "A patient under 10 years old cannot be marked as pregnant. Please verify the age." 
    };
  }
  // ----------------------------------------

  // 1. Negative RDT
  if (testResult === "Negative") {
    treatment = "Give Paracetamol for fever.";
    action = "Look for other causes of fever. If fever persists for 3 days, refer to PHC.";
  } 
  
  // 2. Pregnant Women with Malaria
  else if (isPregnant === "Yes") {
    treatment = "DO NOT give standard ACT or Primaquine.";
    action = "REFER IMMEDIATELY to CHC/Hospital for safe treatment (Quinine).";
  } 
  
  // 3. Plasmodium falciparum (Pf)
  else if (testResult === "Pf_Positive") {
    if (age < 1) {
      treatment = "Artesunate suppository or refer immediately.";
      action = "Refer to hospital.";
    } else {
      treatment = "ACT (Artemether-Lumefantrine) + single dose Primaquine on Day 2.";
      action = "Monitor for 3 days. If vomiting occurs within 1 hour, repeat dose.";
    }
  } 
  
  // 4. Plasmodium vivax (Pv)
  else if (testResult === "Pv_Positive") {
    treatment = "Chloroquine (3 days) + Primaquine (14 days).";
    action = "Check for G6PD deficiency before giving Primaquine. Stop Primaquine if urine turns dark.";
  }

  return { treatment, action };
}