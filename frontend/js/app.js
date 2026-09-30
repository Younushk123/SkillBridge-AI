/* SkillBridge AI - frontend application */

// const API_BASE_URL = window.SKILLBRIDGE_API_URL || "http://127.0.0.1:8000";
const API_BASE_URL =
    window.SKILLBRIDGE_API_URL ||
    "https://skillbridge-ai-backend-mdgs.onrender.com";
const PROFILE_STORAGE_KEY = "skillbridge_profile_id";

const state = {
    activePage: "dashboard",
    profileId: null,
    profile: {
        name: "",
        email: "",
        education: "",
        experienceYears: 0,
        skills: [],
        targetRole: ""
    },
    skillGap: null,
    jobAnalysis: null,
    marketAnalysis: null,
    resumeAnalysis: null
};

function $(selector) { return document.querySelector(selector); }
function $$(selector) { return document.querySelectorAll(selector); }

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function setLoading(button, loading, text) {
    if (!button) return;
    button.disabled = loading;
    button.dataset.originalText ??= button.innerHTML;
    button.innerHTML = loading ? escapeHtml(text) : button.dataset.originalText;
}

function showToast(message) {
    const toast = $("#toast");
    const messageElement = $("#toastMessage");
    if (!toast || !messageElement) return;

    messageElement.textContent = message;
    toast.classList.remove("hidden");

    clearTimeout(showToast.timeout);

    showToast.timeout = setTimeout(
        () => toast.classList.add("hidden"),
        3500
    );
}

function showPage(pageName) {
    $$(".page").forEach(page => page.classList.remove("active"));

    const target = $(`#page-${pageName}`);
    if (target) target.classList.add("active");

    $$(".nav-item").forEach(item => {
        item.classList.toggle(
            "active",
            item.dataset.page === pageName
        );
    });

    state.activePage = pageName;

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

    if (!state.profileId) return;

    if (pageName === "skill-gap" && !state.skillGap) {
        loadSkillGap();
    }

    if (pageName === "market" && !state.marketAnalysis) {
        loadMarketAnalysis();
    }

    if (pageName === "roadmap") {
        renderRoadmap();
    }

    if (pageName === "interview") {
        renderInterview();
    }

    if (pageName === "job-matching") {
        renderJobMatching();
    }
}

function handlePageAction(action) {
    if (action === "profile") {
        openProfileModal();
        return;
    }

    showPage(action);
}

function openProfileModal() {
    const modal = $("#profileModal");
    if (!modal) return;

    populateProfileForm();
    modal.classList.remove("hidden");
}

function closeProfileModal() {
    $("#profileModal")?.classList.add("hidden");
    $("#profileFormError")?.classList.add("hidden");
}

function populateProfileForm() {
    $("#profileInputName").value = state.profile.name || "";
    $("#profileInputEmail").value = state.profile.email || "";
    $("#profileInputEducation").value = state.profile.education || "";
    $("#profileInputExperience").value =
        state.profile.experienceYears || 0;

    const roleSelect = $("#profileInputRole");

    if (
        state.profile.targetRole &&
        ![...roleSelect.options].some(
            o => o.value === state.profile.targetRole
        )
    ) {
        const option = document.createElement("option");
        option.value = state.profile.targetRole;
        option.textContent = state.profile.targetRole;
        roleSelect.appendChild(option);
    }

    roleSelect.value =
        state.profile.targetRole || "Data Scientist";

    setSelectedSkills(state.profile.skills || []);
}

function getSelectedSkills() {
    return [
        ...document.querySelectorAll(
            "#skillsDropdownMenu input[type='checkbox']:checked"
        )
    ].map(checkbox => checkbox.value);
}

function setSelectedSkills(skills) {
    const menu = $("#skillsDropdownMenu");
    const text = $("#skillsDropdownText");

    if (!menu || !text) return;

    const selectedSkills = skills || [];

    menu.querySelectorAll(
        "input[type='checkbox']"
    ).forEach(checkbox => {
        checkbox.checked =
            selectedSkills.includes(checkbox.value);
    });

    selectedSkills.forEach(skill => {
        const exists = [
            ...menu.querySelectorAll(
                "input[type='checkbox']"
            )
        ].some(checkbox => checkbox.value === skill);

        if (!exists) {
            const option = document.createElement("label");

            option.className = "skill-option";

            option.innerHTML = `
                <input type="checkbox" value="${escapeHtml(skill)}" checked>
                <span>${escapeHtml(skill)}</span>
            `;

            menu.appendChild(option);
        }
    });

    updateSkillsDropdownText();
}

function updateSkillsDropdownText() {
    const text = $("#skillsDropdownText");
    if (!text) return;

    const selectedSkills = getSelectedSkills();

    text.textContent = selectedSkills.length
        ? selectedSkills.join(", ")
        : "Select skills";
}

async function loadAvailableSkills() {
    const menu = $("#skillsDropdownMenu");

    if (!menu) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/skills`
        );

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                "Unable to load available skills."
            );
        }

        const skills = Array.isArray(data?.skills)
            ? data.skills
            : [];

        skills.unshift("None");
        skills.push("Others");

        menu.innerHTML = skills.map(skill => `
            <label class="skill-option">
                <input
                    type="checkbox"
                    value="${escapeHtml(skill)}"
                >
                <span>${escapeHtml(skill)}</span>
            </label>
        `).join("");

        setSelectedSkills(
            state.profile.skills || []
        );

    } catch (error) {
        console.error(
            "Skills loading error:",
            error
        );

        menu.innerHTML = `
            <div class="empty-state">
                Unable to load skills.
            </div>
        `;
    }
}

function initializeSkillsDropdown() {
    const dropdown = $("#skillsDropdown");
    const toggle = $("#skillsDropdownToggle");
    const menu = $("#skillsDropdownMenu");

    if (!dropdown || !toggle || !menu) return;

    toggle.addEventListener("click", event => {
        event.stopPropagation();

        const isOpen =
            dropdown.classList.toggle("open");

        toggle.setAttribute(
            "aria-expanded",
            String(isOpen)
        );
    });

    menu.addEventListener("change", event => {
        const changedCheckbox = event.target;

        if (
            !changedCheckbox.matches(
                "input[type='checkbox']"
            )
        ) {
            return;
        }

        const noneCheckbox = menu.querySelector(
            "input[type='checkbox'][value='None']"
        );

        if (
            changedCheckbox.value === "None" &&
            changedCheckbox.checked
        ) {
            menu.querySelectorAll(
                "input[type='checkbox']"
            ).forEach(checkbox => {
                if (checkbox.value !== "None") {
                    checkbox.checked = false;
                }
            });

        } else if (
            changedCheckbox.value !== "None" &&
            changedCheckbox.checked
        ) {
            if (noneCheckbox) {
                noneCheckbox.checked = false;
            }
        }

        updateSkillsDropdownText();
    });

    document.addEventListener("click", event => {
        if (!dropdown.contains(event.target)) {
            dropdown.classList.remove("open");

            toggle.setAttribute(
                "aria-expanded",
                "false"
            );
        }
    });
}

async function handleProfileSubmit(event) {
    event.preventDefault();

    const errorBox = $("#profileFormError");

    errorBox.classList.add("hidden");

    const name =
        $("#profileInputName").value.trim();

    const email =
        $("#profileInputEmail").value.trim();

    const education =
        $("#profileInputEducation").value.trim();

    const experienceYears =
        Number(
            $("#profileInputExperience").value
        ) || 0;

    const targetRole =
        $("#profileInputRole").value;

    const skills = getSelectedSkills();

    if (
        !name ||
        !email ||
        !education ||
        !targetRole ||
        skills.length === 0
    ) {
        errorBox.textContent =
            "Please complete name, email, education, target role, and at least one skill.";

        errorBox.classList.remove("hidden");

        return;
    }

    const profileData = {
        name,
        email,
        education,
        experience_years: experienceYears,
        skills,
        target_role: targetRole
    };

    const isUpdate =
        Boolean(state.profileId);

    const url = isUpdate
        ? `${API_BASE_URL}/profile/${state.profileId}`
        : `${API_BASE_URL}/profile`;

    const method =
        isUpdate ? "PUT" : "POST";

    const button =
        $("#profileForm button[type='submit']");

    try {
        setLoading(
            button,
            true,
            isUpdate
                ? "Updating..."
                : "Creating..."
        );

        const response = await fetch(url, {
            method,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(profileData)
        });

        const data =
            await response.json().catch(() => null);

        if (!response.ok) {
            const detail =
                Array.isArray(data?.detail)
                    ? data.detail
                        .map(e => e.msg)
                        .join("; ")
                    : data?.detail;

            throw new Error(
                detail ||
                "Unable to save profile."
            );
        }

        setProfileFromApi(data);

        localStorage.setItem(
            PROFILE_STORAGE_KEY,
            String(data.id)
        );

        closeProfileModal();

        showPage("dashboard");

        await loadSkillGap();

        showToast(
            isUpdate
                ? "Profile updated successfully."
                : "Profile created successfully."
        );

    } catch (error) {
        console.error(error);

        errorBox.textContent =
            error.message ||
            "Something went wrong.";

        errorBox.classList.remove("hidden");

    } finally {
        setLoading(button, false);
    }
}

function setProfileFromApi(data) {
    state.profileId = data.id;

    state.profile = {
        name: data.name || "",
        email: data.email || "",
        education: data.education || "",
        experienceYears:
            data.experience_years ?? 0,

        skills:
            typeof data.skills === "string"
                ? data.skills
                    .split(",")
                    .map(s => s.trim())
                    .filter(Boolean)
                : (data.skills || []),

        targetRole:
            data.target_role || ""
    };

    updateProfileUI();
}

function updateProfileUI() {
    const profile = state.profile;

    const firstLetter =
        profile.name
            ? profile.name
                .charAt(0)
                .toUpperCase()
            : "Y";

    $("#sidebarAvatar").textContent =
        firstLetter;

    $("#sidebarProfileName").textContent =
        profile.name || "Your Profile";

    $("#sidebarProfileRole").textContent =
        profile.targetRole ||
        "No profile selected";

    $("#profileAvatar").textContent =
        firstLetter;

    $("#profileName").textContent =
        profile.name ||
        "Welcome to SkillBridge";

    $("#profileEducation").textContent =
        profile.education ||
        "Education not provided";

    $("#profileRole").textContent =
        profile.targetRole || "—";

    $("#profileExperience").textContent =
        `${profile.experienceYears || 0} years`;

    $("#metricSkills").textContent =
        profile.skills.length;

    $("#metricRole").textContent =
        profile.targetRole || "—";

    $("#metricGaps").textContent =
        state.skillGap?.missing_skills?.length ?? "—";

    $("#metricJobs").textContent =
        state.marketAnalysis?.jobs_analyzed ?? "—";

    renderDashboardSkills();
}

function renderDashboardSkills() {
    const container =
        $("#dashboardSkills");

    if (!container) return;

    if (!state.profile.skills.length) {
        container.innerHTML =
            `<span class="empty-state">No skills added yet.</span>`;

        return;
    }

    container.innerHTML =
        state.profile.skills
            .map(
                skill =>
                    `<span class="skill-pill">${escapeHtml(skill)}</span>`
            )
            .join("");
}

async function loadProfileFromStorage() {
    const storedId =
        localStorage.getItem(
            PROFILE_STORAGE_KEY
        );

    if (!storedId) return false;

    try {
        const response = await fetch(
            `${API_BASE_URL}/profile/${encodeURIComponent(storedId)}`
        );

        if (!response.ok) {
            localStorage.removeItem(
                PROFILE_STORAGE_KEY
            );

            return false;
        }

        setProfileFromApi(
            await response.json()
        );

        await loadSkillGap();

        return true;

    } catch (error) {
        console.warn(
            "Saved profile could not be restored:",
            error
        );

        return false;
    }
}

async function loadSkillGap() {
    if (!state.profileId) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/profile/${state.profileId}/skill-gap`
        );

        const data =
            await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                "Skill-gap analysis failed."
            );
        }

        state.skillGap = data;

        updateProfileUI();
        renderSkillGap();
        renderRoadmap();

    } catch (error) {
        console.error(
            "Skill gap error:",
            error
        );

        renderErrorCard(
            $("#skillGapContent"),
            error.message
        );
    }
}

function renderSkillGap() {
    const container =
        $("#skillGapContent");

    if (!container || !state.profileId) {
        return;
    }

    const data = state.skillGap;

    if (!data) {
        container.innerHTML = `
            <div class="empty-page">
                <h2>Skill analysis not loaded</h2>
                <p>Analyze your profile to identify career gaps.</p>
            </div>
        `;

        return;
    }

    if (data.error) {
        container.innerHTML = `
            <div class="empty-page">
                <h2>Role not supported</h2>
                <p>${escapeHtml(data.error)}</p>
            </div>
        `;

        return;
    }

    const missing =
        data.missing_skills || [];

    const recommendations =
        data.recommendations || [];

    container.innerHTML = `
        <div class="metrics-grid">

            <div class="metric-card">
                <div class="metric-top">Target Role</div>
                <div class="metric-value">
                    ${escapeHtml(data.target_role)}
                </div>
                <div class="metric-description">
                    Current career target
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">Current Skills</div>
                <div class="metric-value">
                    ${state.profile.skills.length}
                </div>
                <div class="metric-description">
                    Skills in your profile
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">Skill Gaps</div>
                <div class="metric-value">
                    ${missing.length}
                </div>
                <div class="metric-description">
                    Role skills not yet detected
                </div>
            </div>

        </div>

        <div class="metric-card">
            <div class="eyebrow">
                SKILL GAP ANALYSIS
            </div>

            <h2>Skills to develop</h2>

            <div style="margin-top:16px;display:flex;flex-wrap:wrap;gap:8px;">
                ${
                    missing.length
                        ? missing
                            .map(
                                s =>
                                    `<span class="skill-pill">${escapeHtml(s)}</span>`
                            )
                            .join("")
                        : `<span class="empty-state">No gaps detected for this role.</span>`
                }
            </div>
        </div>

        <div class="metric-card">
            <div class="eyebrow">
                LEARNING RECOMMENDATIONS
            </div>

            <h2>What to do next</h2>

            <div style="margin-top:16px;display:flex;flex-direction:column;gap:10px;">
                ${
                    recommendations.length
                        ? recommendations
                            .map(
                                (r, i) =>
                                    `<div class="status-card">
                                        <div class="status-value">
                                            ${i + 1}. ${escapeHtml(r)}
                                        </div>
                                    </div>`
                            )
                            .join("")
                        : `<p class="metric-description">Your current profile covers the selected role baseline.</p>`
                }
            </div>
        </div>
    `;
}

function renderResumeResults(data) {
    const container =
        $("#resumeResults");

    if (!container) return;

    container.classList.remove("hidden");

    const role =
        data.target_role ||
        state.profile.targetRole ||
        "";

    const skills =
        data.skills || [];

    container.innerHTML = `
        <div class="metrics-grid">

            <div class="metric-card">
                <div class="metric-top">Name</div>
                <div class="metric-value">
                    ${escapeHtml(data.name || "—")}
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">Education</div>
                <div class="metric-value">
                    ${escapeHtml(data.education || "—")}
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">Experience</div>
                <div class="metric-value">
                    ${escapeHtml(data.experience_years ?? 0)} yrs
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">Target Role</div>
                <div class="metric-value">
                    ${escapeHtml(role || "—")}
                </div>
            </div>

        </div>

        <div class="metric-card">

            <div class="eyebrow">
                EXTRACTED SKILLS
            </div>

            <h2>Resume intelligence</h2>

            <div style="margin-top:16px;display:flex;flex-wrap:wrap;gap:8px;">
                ${
                    skills.length
                        ? skills
                            .map(
                                s =>
                                    `<span class="skill-pill">${escapeHtml(s)}</span>`
                            )
                            .join("")
                        : `<span class="empty-state">No skills were identified.</span>`
                }
            </div>

            <div style="margin-top:20px;">
                <button
                    class="primary-button"
                    id="useResumeProfile"
                >
                    Use This Profile
                </button>
            </div>

        </div>
    `;

    $("#useResumeProfile")
        .addEventListener(
            "click",
            () => useResumeProfile(data)
        );
}

function useResumeProfile(data) {
    state.profile = {
        ...state.profile,

        name: data.name || "",

        education:
            data.education || "",

        experienceYears:
            data.experience_years || 0,

        skills:
            data.skills || [],

        targetRole:
            data.target_role ||
            state.profile.targetRole ||
            "Data Scientist"
    };

    updateProfileUI();

    openProfileModal();

    showToast(
        "Resume data added to the profile form. Review it and add your email."
    );
}

function handleResumeFileChange(event) {
    const file =
        event.target.files[0];

    $("#resumeFileName").textContent =
        file
            ? file.name
            : "No file selected";
}

async function analyzeResume() {
    const file =
        $("#resumeFile").files[0];

    if (!file) {
        return showToast(
            "Please select a PDF resume first."
        );
    }

    if (
        file.type &&
        file.type !== "application/pdf" &&
        !file.name
            .toLowerCase()
            .endsWith(".pdf")
    ) {
        return showToast(
            "Please upload a PDF file."
        );
    }

    if (
        !file.name
            .toLowerCase()
            .endsWith(".pdf")
    ) {
        return showToast(
            "Please upload a PDF file."
        );
    }

    if (file.size > 5 * 1024 * 1024) {
        return showToast(
            "Resume file must be 5 MB or smaller."
        );
    }

    const button =
        $("#analyzeResumeButton");

    setLoading(
        button,
        true,
        "Analyzing Resume..."
    );

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/resume/analyze`,
                {
                    method: "POST",
                    body: formData
                }
            );

        const data =
            await response.json()
                .catch(() => null);

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                "Resume analysis failed."
            );
        }

        state.resumeAnalysis =
            data;

        renderResumeResults(data);

        showToast(
            "Resume analyzed successfully."
        );

    } catch (error) {
        console.error(error);

        showToast(
            error.message ||
            "Resume analysis failed."
        );

    } finally {
        setLoading(
            button,
            false
        );
    }
}

function jobInputTemplate() {
    return `
        <div class="metric-card">

            <div class="eyebrow">
                JOB DESCRIPTION ANALYSIS
            </div>

            <h2>
                Compare your profile with a real opportunity
            </h2>

            <p
                class="metric-description"
                style="margin-top:8px;"
            >
                Paste the job description below.
                Required and preferred skills will
                be separated automatically.
            </p>

            <textarea
                id="jobDescriptionInput"
                rows="10"
                placeholder="Paste the complete job description here..."
            ></textarea>

            <div style="margin-top:14px;">
                <button
                    class="primary-button"
                    id="analyzeJobButton"
                >
                    Analyze Job Description
                    <span>→</span>
                </button>
            </div>

            <div
                id="jobFormError"
                class="form-error hidden"
                style="margin-top:12px;"
            ></div>

        </div>
    `;
}

function renderJobMatching() {
    const container =
        $("#jobMatchingContent");

    if (!container) return;

    if (!state.profileId) {
        container.innerHTML = `
            <div class="empty-page">

                <div class="empty-page-icon">
                    ◎
                </div>

                <h2>
                    Create your profile first
                </h2>

                <p>
                    Your profile is required
                    to calculate job compatibility.
                </p>

                <button
                    class="primary-button"
                    data-page-action="profile"
                >
                    Create Profile
                </button>

            </div>
        `;

        container
            .querySelector(
                "[data-page-action='profile']"
            )
            .addEventListener(
                "click",
                () => openProfileModal()
            );

        return;
    }

    const result =
        state.jobAnalysis;

    container.innerHTML =
        jobInputTemplate();

    if (result) {
        const d = result;

        container.innerHTML += `
            <div class="metrics-grid">

                <div class="metric-card">
                    <div class="metric-top">
                        Match Score
                    </div>

                    <div class="metric-value">
                        ${d.match_score}%
                    </div>

                    <div class="metric-description">
                        Required-skill compatibility
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-top">
                        Required
                    </div>

                    <div class="metric-value">
                        ${(d.required_skills || []).length}
                    </div>

                    <div class="metric-description">
                        Skills requested
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-top">
                        Matched
                    </div>

                    <div class="metric-value">
                        ${(d.matched_skills || []).length}
                    </div>

                    <div class="metric-description">
                        Skills you have
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-top">
                        Missing
                    </div>

                    <div class="metric-value">
                        ${(d.missing_skills || []).length}
                    </div>

                    <div class="metric-description">
                        Skills to develop
                    </div>
                </div>

            </div>

            <div class="metric-card">

                <div class="eyebrow">
                    REQUIREMENTS
                </div>

                <h2>
                    Required skills
                </h2>

                <div
                    style="margin-top:14px;display:flex;flex-wrap:wrap;gap:8px;"
                >
                    ${skillPillsHtml(
                        d.required_skills,
                        "No required skills detected."
                    )}
                </div>

                <h2 style="margin-top:20px;">
                    Preferred skills
                </h2>

                <div
                    style="margin-top:14px;display:flex;flex-wrap:wrap;gap:8px;"
                >
                    ${skillPillsHtml(
                        d.preferred_skills,
                        "No preferred skills detected."
                    )}
                </div>

            </div>

            <div class="metric-card">

                <div class="eyebrow">
                    YOUR MATCH
                </div>

                <h2>
                    Matched and missing skills
                </h2>

                <p
                    class="metric-description"
                    style="margin-top:14px;"
                >
                    Matched
                </p>

                <div
                    style="margin-top:8px;display:flex;flex-wrap:wrap;gap:8px;"
                >
                    ${skillPillsHtml(
                        d.matched_skills,
                        "No matched skills."
                    )}
                </div>

                <p
                    class="metric-description"
                    style="margin-top:16px;"
                >
                    Missing
                </p>

                <div
                    style="margin-top:8px;display:flex;flex-wrap:wrap;gap:8px;"
                >
                    ${skillPillsHtml(
                        d.missing_skills,
                        "No missing skills."
                    )}
                </div>

            </div>

            <div class="metric-card">

                <div class="eyebrow">
                    LEARNING PRIORITIES
                </div>

                <h2>
                    Prioritized preparation
                </h2>

                <div
                    style="margin-top:14px;display:flex;flex-direction:column;gap:10px;"
                >
                    ${
                        (d.learning_priorities || [])
                            .map(
                                (p, i) =>
                                    `<div class="status-card">
                                        <div class="status-label">
                                            ${escapeHtml(p.priority)}
                                            ·
                                            ${escapeHtml(p.requirement_type)}
                                        </div>

                                        <div class="status-value">
                                            ${i + 1}.
                                            ${escapeHtml(p.skill)}
                                        </div>

                                        <div class="feature-description">
                                            ${escapeHtml(p.recommendation)}
                                        </div>
                                    </div>`
                            )
                            .join("")
                        ||
                        `<p class="metric-description">
                            No learning priorities were generated.
                        </p>`
                    }
                </div>

            </div>
        `;
    }

    const button =
        $("#analyzeJobButton");

    if (button) {
        button.addEventListener(
            "click",
            submitJobAnalysis
        );
    }

    const textarea =
        $("#jobDescriptionInput");

    if (
        textarea &&
        state.jobDescriptionDraft
    ) {
        textarea.value =
            state.jobDescriptionDraft;
    }
}

function skillPillsHtml(
    skills,
    emptyText
) {
    return skills?.length
        ? skills
            .map(
                s =>
                    `<span class="skill-pill">${escapeHtml(s)}</span>`
            )
            .join("")
        : `<span class="empty-state">${escapeHtml(emptyText)}</span>`;
}

async function submitJobAnalysis() {
    const textarea =
        $("#jobDescriptionInput");

    const errorBox =
        $("#jobFormError");

    const jobDescription =
        textarea?.value.trim() || "";

    state.jobDescriptionDraft =
        jobDescription;

    if (jobDescription.length < 20) {
        errorBox.textContent =
            "Please paste at least 20 characters of job-description text.";

        errorBox.classList.remove("hidden");

        return;
    }

    errorBox.classList.add("hidden");

    const button =
        $("#analyzeJobButton");

    setLoading(
        button,
        true,
        "Analyzing..."
    );

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/profile/${state.profileId}/job-analysis`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        job_description:
                            jobDescription
                    })
                }
            );

        const data =
            await response.json()
                .catch(() => null);

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                "Job analysis failed."
            );
        }

        state.jobAnalysis =
            data;

        renderJobMatching();
        renderRoadmap();
        renderInterview();

        showToast(
            "Job description analyzed successfully."
        );

    } catch (error) {
        console.error(error);

        errorBox.textContent =
            error.message ||
            "Job analysis failed.";

        errorBox.classList.remove("hidden");

    } finally {
        setLoading(
            button,
            false
        );
    }
}

async function loadMarketAnalysis() {
    if (!state.profileId) {
        renderMarketAnalysis();
        return;
    }

    const container =
        $("#marketContent");

    if (container) {
        container.innerHTML = `
            <div class="empty-page">

                <h2>
                    Analyzing the market...
                </h2>

                <p>
                    We're fetching the latest job market data.
                    This may take a moment.
                </p>

            </div>
        `;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/profile/${state.profileId}/market-analysis`
            );

        const data =
            await response.json()
                .catch(() => null);

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                "Market analysis failed."
            );
        }

        state.marketAnalysis =
            data;

        updateProfileUI();
        renderMarketAnalysis();

    } catch (error) {
        console.error(error);

        renderErrorCard(
            $("#marketContent"),
            error.message
        );
    }
}

function renderMarketAnalysis() {
    const container =
        $("#marketContent");

    if (!container) return;

    if (!state.profileId) {
        container.innerHTML = `
            <div class="empty-page">

                <h2>
                    Create your profile first
                </h2>

                <p>
                    Market analysis needs a target role and current skills.
                </p>

                <button
                    class="primary-button"
                    data-page-action="profile"
                >
                    Create Profile
                </button>

            </div>
        `;

        container
            .querySelector("button")
            .addEventListener(
                "click",
                openProfileModal
            );

        return;
    }

    const data =
        state.marketAnalysis;

    if (!data) {
        container.innerHTML = `
            <div class="empty-page">

                <h2>
                    Market intelligence
                </h2>

                <p>
                    Analyze recent job listings for your target role.
                </p>

                <button
                    class="primary-button"
                    id="analyzeMarketButton"
                >
                    Analyze Current Market
                </button>

            </div>
        `;

        container
            .querySelector("button")
            .addEventListener(
                "click",
                loadMarketAnalysis
            );

        return;
    }

    container.innerHTML = `

        <div class="metrics-grid">

            <div class="metric-card">
                <div class="metric-top">
                    Jobs Analyzed
                </div>

                <div class="metric-value">
                    ${data.jobs_analyzed}
                </div>

                <div class="metric-description">
                    Recent job descriptions
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">
                    Market Skills
                </div>

                <div class="metric-value">
                    ${(data.market_skills || []).length}
                </div>

                <div class="metric-description">
                    Detected demand signals
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">
                    Target Role
                </div>

                <div class="metric-value">
                    ${escapeHtml(data.target_role)}
                </div>

                <div class="metric-description">
                    Market analysis context
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">
                    Top Skills
                </div>

                <div class="metric-value">
                    ${Math.min(
                        5,
                        (data.market_skills || []).length
                    )}
                </div>

                <div class="metric-description">
                    Highest-demand skills shown
                </div>
            </div>

        </div>

        <div class="metric-card">

            <div class="eyebrow">
                TOP IN-DEMAND SKILLS
            </div>

            <h2>
                Market demand
            </h2>

            <div
                style="margin-top:16px;display:flex;flex-direction:column;gap:10px;"
            >

                ${
                    (data.market_skills || [])
                        .slice(0, 15)
                        .map(item => `
                            <div class="status-card">

                                <div
                                    style="display:flex;justify-content:space-between;gap:12px;"
                                >

                                    <div class="status-value">
                                        ${escapeHtml(item.skill)}
                                    </div>

                                    <div class="feature-description">
                                        ${item.demand_percentage}%
                                        ·
                                        ${item.demand_count}
                                        jobs
                                    </div>

                                </div>

                                <div
                                    style="margin-top:8px;height:6px;background:#182235;border-radius:99px;overflow:hidden;"
                                >
                                    <div
                                        style="height:100%;width:${Math.min(
                                            100,
                                            Math.max(
                                                0,
                                                item.demand_percentage
                                            )
                                        )}%;background:#4f8cff;"
                                    ></div>
                                </div>

                            </div>
                        `)
                        .join("")
                    ||
                    `<p class="metric-description">
                        No supported skills were detected in the available job descriptions.
                    </p>`
                }

            </div>

        </div>

        <div class="metric-card">

            <div class="eyebrow">
                IN-DEMAND CAREER ROLES
            </div>

            <h2>
                Career demand signals
            </h2>

            <div
                style="margin-top:14px;display:flex;flex-direction:column;gap:12px;"
            >

                ${
                    (data.role_demand || [])
                        .map(item => `
                            <div
                                style="display:flex;justify-content:space-between;align-items:center;gap:16px;"
                            >
                                <span>
                                    ${escapeHtml(item.role)}
                                </span>

                                <span>
                                    ${item.demand_percentage}%
                                    ·
                                    ${item.job_count}
                                    jobs
                                </span>
                            </div>
                        `)
                        .join("")
                }

            </div>

        </div>

        <div class="metric-card">

            <div class="eyebrow">
                AI MARKET INSIGHT
            </div>

            <h4>
                ${escapeHtml(data.market_summary)}
            </h4>

        </div>
    `;
}

function renderRoadmap() {
    const container =
        $("#roadmapContent");

    if (!container) return;

    if (!state.profileId) {
        container.innerHTML = `
            <div class="empty-page">

                <h2>
                    Your roadmap starts here
                </h2>

                <p>
                    Create a profile and analyze your skills or a job description.
                </p>

                <button
                    class="primary-button"
                    data-page-action="profile"
                >
                    Create Profile
                </button>

            </div>
        `;

        container
            .querySelector("button")
            .addEventListener(
                "click",
                openProfileModal
            );

        return;
    }

    let roadmap =
        state.jobAnalysis?.roadmap || null;

    if (
        !roadmap &&
        state.skillGap?.missing_skills?.length
    ) {
        const missing =
            state.skillGap.missing_skills;

        roadmap = [
            {
                title: "Close Skill Gaps",
                duration: "Weeks 1–2",
                focus_skills:
                    missing.slice(0, 3),

                actions:
                    missing
                        .slice(0, 3)
                        .map(
                            s =>
                                `Study ${s} fundamentals and complete a practical exercise.`
                        )
            },

            {
                title: "Build Evidence",
                duration: "Week 3",
                focus_skills:
                    missing.slice(3, 6),

                actions: [
                    "Build a small portfolio project that demonstrates the skills."
                ]
            },

            {
                title: "Prepare for Roles",
                duration: "Week 4",
                focus_skills:
                    state.profile.skills.slice(0, 3),

                actions: [
                    "Document project outcomes and prepare interview examples."
                ]
            }
        ];
    }

    if (!roadmap) {
        container.innerHTML = `
            <div class="empty-page">

                <h2>
                    Analyze your skills first
                </h2>

                <p>
                    The roadmap is generated from your skill gaps or a specific job analysis.
                </p>

                <button
                    class="primary-button"
                    data-page-action="skill-gap"
                >
                    Analyze Skills
                </button>

            </div>
        `;

        container
            .querySelector("button")
            .addEventListener(
                "click",
                () => showPage("skill-gap")
            );

        return;
    }

    container.innerHTML = `
        <div class="metrics-grid">

            <div class="metric-card">
                <div class="metric-top">
                    Target Role
                </div>

                <div class="metric-value">
                    ${escapeHtml(
                        state.profile.targetRole
                    )}
                </div>

                <div class="metric-description">
                    Roadmap context
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-top">
                    Phases
                </div>

                <div class="metric-value">
                    ${roadmap.length}
                </div>

                <div class="metric-description">
                    Structured preparation stages
                </div>
            </div>

        </div>

        <div
            style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;"
        >

            ${roadmap.map((phase, i) => `
                <div class="metric-card">

                    <div class="eyebrow">
                        PHASE ${i + 1}
                    </div>

                    <h2>
                        ${escapeHtml(phase.title)}
                    </h2>

                    <p
                        class="metric-description"
                        style="margin-top:6px;"
                    >
                        ${escapeHtml(phase.duration)}
                    </p>

                    <div
                        style="margin-top:16px;display:flex;flex-wrap:wrap;gap:8px;"
                    >
                        ${skillPillsHtml(
                            phase.focus_skills,
                            "No specific skills."
                        )}
                    </div>

                    <div style="margin-top:16px;">

                        <div class="eyebrow">
                            RECOMMENDED ACTIONS
                        </div>

                        <div
                            style="margin-top:10px;display:flex;flex-direction:column;gap:8px;"
                        >

                            ${(phase.actions || [])
                                .map(a => `
                                    <div class="status-card">
                                        <div class="status-value">
                                            → ${escapeHtml(a)}
                                        </div>
                                    </div>
                                `)
                                .join("")}

                        </div>

                    </div>

                </div>
            `).join("")}

        </div>
    `;
}

async function renderInterview() {
    const container = $("#interviewContent");

    if (!container) return;

    if (!state.profileId) {
        container.innerHTML = `
            <div class="empty-page">
                <h2>Create your profile first</h2>
                <p>Interview preparation is generated from your career profile and job requirements.</p>
                <button class="primary-button" id="createInterviewProfile">
                    Create Profile
                </button>
            </div>
        `;

        const button = $("#createInterviewProfile");

        if (button) {
            button.addEventListener("click", openProfileModal);
        }

        return;
    }

    container.innerHTML = `
        
        <div style="display:flex;flex-direction:column;gap:16px;">

            <div class="metric-card">
                <div class="eyebrow">YOUR TARGET ROLE</div>

                <h2 style="margin-top:8px;">
                    ${escapeHtml(state.profile?.targetRole || "target role")}
                </h2>

                <p class="metric-description" style="margin-top:8px;">
                    Generate AI-powered interview questions based on your current skills and skill gaps.
                </p>

                <button class="primary-button" id="generateProfileInterview"style="margin-top:12px;">
                    Generate Interview Questions
                </button>
            </div>

            <div class="metric-card">
                <div class="eyebrow">REAL JOB</div>

                <h2 style="margin-top:8px;">
                    Prepare from a Real Job
                </h2>

                <p class="metric-description" style="margin-top:8px;">
                    Generate interview questions based on your analyzed job description.
                </p>

                <button
                    class="secondary-button"
                    id="generateJobInterview"
                    style="margin-top:12px;"
                >
                    Generate Job-Specific Questions
                </button>
            </div>

        </div>
    `;

    const generateButton = $("#generateProfileInterview");

    if (generateButton) {
        generateButton.addEventListener("click", loadProfileInterview);
    }

    const jobButton = $("#generateJobInterview");

    if (jobButton) {
        jobButton.addEventListener(
            "click",
            loadJobInterview
        );
    }
}

async function loadProfileInterview() {
    const container = $("#interviewContent");

    const button = $("#generateProfileInterview");

    setLoading(
        button,
        true,
        "Generating Questions..."
    );

    if (!container || !state.profileId) return;
    try {
        const response = await fetch(
            `${API_BASE_URL}/profile/${state.profileId}/interview`
        );

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(
                data?.detail || "Unable to generate interview questions."
            );
        }

        const questions = Array.isArray(data) ? data : [];

        if (!questions.length) {
            throw new Error("No interview questions were generated.");
        }

        container.innerHTML = `
            <div class="metric-card">
                <div class="eyebrow">INTERVIEW QUESTIONS</div>

                <h2>${questions.length} personalized questions</h2>

                <p class="metric-description" style="margin-top:8px;">
                    Generated for your
                    ${escapeHtml(state.profile?.targetRole || "target role")}
                    using your current skills and skill gaps.
                </p>
            </div>

            <div style="display:flex;flex-direction:column;gap:12px;">

                ${questions.map((item, index) => `
                    <div class="metric-card">

                        <div class="eyebrow">
                            ${index + 1}. ${escapeHtml(item.skill)}
                        </div>

                        <h4 style="margin-top:8px;">
                            ${escapeHtml(item.question)}
                        </h4>

                    </div>
                `).join("")}

            </div>
        `;

    } catch (error) {
        console.error("Interview generation error:", error);

        container.innerHTML = `
            <div class="empty-page">
                <h2>Unable to generate questions</h2>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "Something went wrong while generating interview questions."
                    )}
                </p>

                <button class="primary-button" id="retryProfileInterview">
                    Try Again
                </button>
            </div>
        `;

        const retryButton = $("#retryProfileInterview");

        if (retryButton) {
            retryButton.addEventListener("click", loadProfileInterview);
        }
    } finally {
        setLoading(button, false);
    }
}

async function loadJobInterview() {
    const container = $("#interviewContent");
    const button = $("#generateJobInterview");

    if (!container || !state.profileId) return;

    const jobDescription = state.jobDescriptionDraft?.trim() || "";

    if (jobDescription.length < 20) {
        container.innerHTML = `
            <div class="empty-page">
                <h2>Analyze a job first</h2>
                <p>
                    Please analyze a job description before generating
                    job-specific interview questions.
                </p>
            </div>
        `;
        return;
    }

    setLoading(
        button,
        true,
        "Generating Questions..."
    );

    try {
        const response = await fetch(
            `${API_BASE_URL}/profile/${state.profileId}/job-interview`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    job_description: jobDescription
                })
            }
        );

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                "Unable to generate job-specific interview questions."
            );
        }

        const questions = Array.isArray(data) ? data : [];

        if (!questions.length) {
            throw new Error(
                "No job-specific interview questions were generated."
            );
        }

        container.innerHTML = `
            <div class="metric-card">
                <div class="eyebrow">REAL JOB INTERVIEW</div>

                <h2>${questions.length} job-specific questions</h2>

                <p class="metric-description" style="margin-top:8px;">
                    Generated for your
                    ${escapeHtml(state.profile?.targetRole || "target role")}
                    based on the analyzed job description.
                </p>
            </div>

            <div style="display:flex;flex-direction:column;gap:12px;">

                ${questions.map((item, index) => `
                    <div class="metric-card">

                        <div class="eyebrow">
                            ${index + 1}. ${escapeHtml(item.skill)}
                        </div>

                        <h2 style="margin-top:8px;">
                            ${escapeHtml(item.question)}
                        </h2>

                    </div>
                `).join("")}

            </div>
        `;

    } catch (error) {
        console.error(
            "Job interview generation error:",
            error
        );

        container.innerHTML = `
            <div class="empty-page">
                <h2>Unable to generate questions</h2>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "Something went wrong while generating job-specific interview questions."
                    )}
                </p>

                <button
                    class="primary-button"
                    id="retryJobInterview"
                >
                    Try Again
                </button>
            </div>
        `;

        const retryButton = $("#retryJobInterview");

        if (retryButton) {
            retryButton.addEventListener(
                "click",
                loadJobInterview
            );
        }

    } finally {
        setLoading(
            button,
            false
        );
    }
}

function renderErrorCard(
    container,
    message
) {
    if (!container) return;

    container.innerHTML = `
        <div class="empty-page">

            <h2>
                Something went wrong
            </h2>

            <p>
                ${escapeHtml(
                    message ||
                    "Unable to load this analysis."
                )}
            </p>

            <button
                class="primary-button"
                id="retryAnalysis"
            >
                Try Again
            </button>

        </div>
    `;

    container
        .querySelector("button")
        ?.addEventListener(
            "click",
            () => {
                if (
                    container.id ===
                    "marketContent"
                ) {
                    loadMarketAnalysis();

                } else if (
                    container.id ===
                    "skillGapContent"
                ) {
                    loadSkillGap();
                }
            }
        );
}

function initializeEventListeners() {
    $$(".nav-item").forEach(item => {
        item.addEventListener(
            "click",
            () => showPage(
                item.dataset.page
            )
        );
    });

    $$("[data-page-action]")
        .forEach(element => {
            element.addEventListener(
                "click",
                () =>
                    handlePageAction(
                        element.dataset.pageAction
                    )
            );
        });

    $("#closeProfileModal")
        ?.addEventListener(
            "click",
            closeProfileModal
        );

    $("#cancelProfile")
        ?.addEventListener(
            "click",
            closeProfileModal
        );

    $("#profileForm")
        ?.addEventListener(
            "submit",
            handleProfileSubmit
        );

    $("#resumeFile")
        ?.addEventListener(
            "change",
            handleResumeFileChange
        );

    $("#analyzeResumeButton")
        ?.addEventListener(
            "click",
            analyzeResume
        );

    initializeSkillsDropdown();
}

async function initializeApp() {
    initializeEventListeners();

    await loadAvailableSkills();

    updateProfileUI();

    showPage("dashboard");
}

document.addEventListener(
    "DOMContentLoaded",
    initializeApp
);