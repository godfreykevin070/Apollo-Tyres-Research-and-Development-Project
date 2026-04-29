// Copy ftire.js content and replace all instances of 'ftire' with 'cdtire' in the API endpoints

document.getElementById('logoutBtn').addEventListener('click', function() {
    window.location.href = '/login.html';
});

// Add after the logout button handler (around line 10):

// Helper to get project ID
function getProjectId() {
    const urlParams = new URLSearchParams(window.location.search);
    let pid = urlParams.get('projectId');
    if (!pid) {
        pid = sessionStorage.getItem('currentProjectId');
    }
    return pid;
}

function getProjectIdFromURL() {
    return getProjectId();
}

// Add after line 16:

// ===== Optional Parameters Dropdown System =====

const parameterDefinitions = {
    nominalWidth: {
        label: 'Nominal Width',
        id: 'nominalWidth',
        placeholder: 'Enter NW value in mm',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    outerDiameter: {
        label: 'Outer Diameter',
        id: 'outerDiameter',
        placeholder: 'Enter OD value in mm',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    l2: {
        label: 'Load 2',
        id: 'l2',
        placeholder: 'Enter L2 value in Kg',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    l3: {
        label: 'Load 3',
        id: 'l3',
        placeholder: 'Enter L3 value in Kg',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    l4: {
        label: 'Load 4',
        id: 'l4',
        placeholder: 'Enter L4 value in Kg',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    l5: {
        label: 'Load 5',
        id: 'l5',
        placeholder: 'Enter L5 value in Kg',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    vel: {
        label: 'Test Speed',
        id: 'vel',
        placeholder: 'Enter velocity in kmph',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    ia: {
        label: 'Inclination Angle',
        id: 'ia',
        placeholder: 'Enter IA value in degree',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    sr: {
        label: 'Slip Ratio',
        id: 'sr',
        placeholder: 'Enter SR value in %',
        pattern: '[0-9]*\\.?[0-9]+'
    },
    aspectRatio: {
        label: 'Aspect Ratio',
        id: 'aspectRatio',
        placeholder: 'Enter AR value in %',
        pattern: '[0-9]*\\.?[0-9]+'
    }
};

const addedParams = new Set();

// Toggle dropdown visibility
document.getElementById('addParamBtn').addEventListener('click', function() {
    const dropdown = document.getElementById('paramDropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
});

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {
    const dropdown = document.getElementById('paramDropdown');
    const addBtn = document.getElementById('addParamBtn');
    
    if (!dropdown.contains(e.target) && e.target !== addBtn && !addBtn.contains(e.target)) {
        dropdown.style.display = 'none';
    }
});

// Handle parameter selection from dropdown
document.querySelectorAll('.dropdown-item').forEach(item => {
    item.addEventListener('click', function() {
        const paramKey = this.getAttribute('data-param');
        
        if (addedParams.has(paramKey)) {
            return; // Already added
        }
        
        addParameter(paramKey);
        this.classList.add('added');
        addedParams.add(paramKey);
        
        // Close dropdown after selection
        document.getElementById('paramDropdown').style.display = 'none';
    });
});

function addParameter(paramKey) {
    const param = parameterDefinitions[paramKey];
    const container = document.getElementById('optionalInputsContainer');
    
    const wrapper = document.createElement('div');
    wrapper.className = 'input-group optional-input-wrapper';
    wrapper.setAttribute('data-param', paramKey);
    
    wrapper.innerHTML = `
        <button type="button" class="remove-param-btn" data-param="${paramKey}">×</button>
        <h3>${param.label}</h3>
        <div class="input-row">
            <label for="${param.id}">${param.id.toUpperCase()}:</label>
            <input type="text" id="${param.id}" name="${param.id}" 
                   placeholder="${param.placeholder}" 
                   pattern="${param.pattern}">
        </div>
    `;
    
    container.appendChild(wrapper);
    
    // Add remove button handler
    wrapper.querySelector('.remove-param-btn').addEventListener('click', function() {
        removeParameter(paramKey);
    });
}

function removeParameter(paramKey) {
    const wrapper = document.querySelector(`.optional-input-wrapper[data-param="${paramKey}"]`);
    if (wrapper) {
        wrapper.remove();
    }
    
    addedParams.delete(paramKey);
    
    // Re-enable in dropdown
    const dropdownItem = document.querySelector(`.dropdown-item[data-param="${paramKey}"]`);
    if (dropdownItem) {
        dropdownItem.classList.remove('added');
    }
}

// ===== End Optional Parameters System =====

// Replace the submit button validation (lines 145-175):

document.getElementById('submitBtn').addEventListener('click', async function() {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = '';
    errorMessage.style.display = 'none';
    
    //  Only validate mandatory fields that MUST exist
    const mandatoryFields = ['rimWidth', 'rimDiameter', 'p1', 'l1'];
    let allValid = true;
    let missingFields = [];
    
    mandatoryFields.forEach(fieldId => {
        const input = document.getElementById(fieldId);
        if (!input) {
            console.error(`❌ Mandatory field "${fieldId}" not found in DOM`);
            allValid = false;
            missingFields.push(fieldId);
            return;
        }
        
        if (!input.value || !input.checkValidity()) {
            allValid = false;
            input.classList.add('invalid');
            missingFields.push(fieldId);
        } else {
            input.classList.remove('invalid');
        }
    });

    //  Validate ONLY optional fields that were actually added
    const optionalContainer = document.getElementById('optionalInputsContainer');
    if (optionalContainer) {
        const optionalInputs = optionalContainer.querySelectorAll('input');
        optionalInputs.forEach(input => {
            // Only validate if user entered a value
            if (input.value && input.value.trim() !== '') {
                if (!input.checkValidity()) {
                    allValid = false;
                    input.classList.add('invalid');
                }
            } else {
                // Remove validation styling if empty
                input.classList.remove('invalid');
            }
        });
    }

    if (!allValid) {
        errorMessage.textContent = `❌ Please fill in all mandatory fields: ${missingFields.join(', ')}`;
        errorMessage.style.display = 'block';
        errorMessage.style.color = '#dc3545';
        return;
    }
    
    // Persist current input values
    try {
        const pid = getProjectId();
        if (pid) {
            const allFieldIds = ['rimWidth', 'rimDiameter', 'p1', 'l1'];
            
            // Add optional field IDs that were actually added
            addedParams.forEach(paramKey => {
                const fieldId = parameterDefinitions[paramKey]?.id;
                if (fieldId) allFieldIds.push(fieldId);
            });
            
            await saveInputs(pid, collectInputs(allFieldIds));
            console.log('✅ Saved inputs for project:', pid);
        }
    } catch (e) {
        console.warn('⚠️ Failed to save inputs:', e);
    }

    const projectName = sessionStorage.getItem('currentProject') || 'DefaultProject';
    checkProjectExists(projectName, 'CDTire');
});

// Add function to check project existence and show confirmation
function checkProjectExists(projectName, protocol) {
    fetch('/api/check-project-exists', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            projectName: projectName,
            protocol: protocol
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.message || 'Error checking project existence');
        }
        
        // ✅ ONLY show prompt if project EXISTS IN DATABASE
        if (data.exists && data.project && data.project.id) {
            // Project exists, show confirmation dialog
            const userConfirmed = confirm(`Project "${data.folderName}" already exists. Do you want to Replace it?`);
            if (userConfirmed) {
                // User confirmed, proceed with workflow
                proceedWithSubmission();
            } else {
                // User cancelled, do nothing (stay on same page)
                return;
            }
        } else {
            // Project doesn't exist, proceed normally
            proceedWithSubmission();
        }
    })
    .catch(error => {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.style.color = '#d9534f';
        errorMessage.textContent = error.message || 'Error checking project status. Please try again.';
    });
}



async function proceedWithSubmission() {
    //  ADD DEBUG LOGS:
    console.log('🚀 Starting CDTire submission...');
    console.log('Project Name:', sessionStorage.getItem('currentProject'));
    console.log('Project ID:', sessionStorage.getItem('currentProjectId'));
    console.log('Protocol:', sessionStorage.getItem('currentProtocol'));
    
    // Check mandatory fields
    const rimWidth = document.getElementById('rimWidth')?.value;
    const rimDiameter = document.getElementById('rimDiameter')?.value;
    const p1 = document.getElementById('p1')?.value;
    const l1 = document.getElementById('l1')?.value;
    
    console.log('Mandatory values:', { rimWidth, rimDiameter, p1, l1 });

    const meshFile = document.getElementById('meshFile').files[0];
    const errorMessage = document.getElementById('errorMessage');
    
    // Clear previous errors
    errorMessage.textContent = '';
    errorMessage.style.display = 'none'; //  ADD THIS
    
    if (meshFile) {
        const formData = new FormData();
        formData.append('meshFile', meshFile);
        
        try {
            const response = await fetch('/api/upload-mesh-file', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to upload mesh file');
            }

            console.log('✅ Mesh file uploaded successfully');
            
            //  ADD RETURN HERE - this was missing!
            return await processCDTireExcel(); //  RETURN THE PROMISE
            
        } catch (error) {
            errorMessage.style.color = '#d9534f';
            errorMessage.style.display = 'block';
            errorMessage.textContent = error.message || 'Error uploading mesh file. Please try again.';
            console.error('Mesh file upload error:', error);
            throw error; //  Re-throw to stop execution
        }
    } else {
        //  RETURN THE PROMISE
        return await processCDTireExcel();
    }
}



function updateTestSummary() {
    fetch('/api/get-cdtire-summary')
        .then(response => {
            if (!response.ok) {
                console.error('Summary response status:', response.status);
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Summary data received:', data); // Debug log
            const summaryContainer = document.getElementById('testSummary');
            if (!data || data.length === 0) {
                summaryContainer.innerHTML = '<div class="summary-item">No tests available</div>';
                return;
            }
            
            summaryContainer.innerHTML = data.map(item => `
                <div class="summary-item">
                    <span class="test-name">${item.test_name || 'Unknown'}:</span>
                    <span class="test-count">${item.count}</span>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error fetching test summary:', error);
            const summaryContainer = document.getElementById('testSummary');
            summaryContainer.innerHTML = '<div class="error-message">Unable to load test summary</div>';
        });
}// Replace the processCDTireExcel function:

async function processCDTireExcel() {
    const errorMessage = document.getElementById('errorMessage');
    
    console.log('📊 Starting Excel processing...');
    
    const parameterData = {
        // ✅ Mandatory fields - direct access with fallback
        pressure1: document.getElementById('p1')?.value || '',
        load1_kg: document.getElementById('l1')?.value || '',
        width: document.getElementById('rimWidth')?.value || '',
        diameter: document.getElementById('rimDiameter')?.value || '',
        
        // ✅ Optional fields
        load2_kg: '',
        load3_kg: '',
        load4_kg: '',
        load5_kg: '',
        speed_kmph: '',
        IA: '',
        SR: '',
        Outer_diameter: '',
        nomwidth: '',
        aspratio: ''
    };

    // ✅ Safely populate optional fields
    const optionalFields = {
        'l2': 'load2_kg',
        'l3': 'load3_kg',
        'l4': 'load4_kg',
        'l5': 'load5_kg',
        'vel': 'speed_kmph',
        'ia': 'IA',
        'sr': 'SR',
        'outerDiameter': 'Outer_diameter',
        'nominalWidth': 'nomwidth',
        'aspectRatio': 'aspratio'
    };

    Object.keys(optionalFields).forEach(inputId => {
        const element = document.getElementById(inputId);
        if (element && element.value) {
            const paramKey = optionalFields[inputId];
            parameterData[paramKey] = element.value.trim();
        }
    });

    // ✅ Validate mandatory fields
    if (!parameterData.pressure1 || !parameterData.load1_kg || !parameterData.width || !parameterData.diameter) {
        const error = new Error('Mandatory fields (Rim Width, Rim Diameter, Pressure, Load 1) must be filled');
        errorMessage.textContent = error.message;
        errorMessage.style.display = 'block';
        throw error;
    }

    console.log('📊 Collected parameters:', parameterData);

    try {
        //  STEP 1: Generate parameter file
        console.log('📝 Step 1: Generating parameters.inc...');
        const paramResponse = await fetch('/api/generate-parameters', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(parameterData)
        });
        
        const paramData = await paramResponse.json();
        if (!paramData.success) throw new Error(paramData.message);
        console.log('✅ parameters.inc generated');

        //  STEP 2: Read protocol Excel
        console.log('📖 Step 2: Reading protocol Excel...');
        const excelResponse = await fetch('/api/read-protocol-excel', {
            headers: { 'Referer': '/cdtire.html' }
        });
        
        if (!excelResponse.ok) {
            throw new Error(`Failed to read Excel: ${excelResponse.status}`);
        }
        
        const arrayBuffer = await excelResponse.arrayBuffer();
        console.log('✅ Excel file loaded');

        //  STEP 3: Process Excel with XLSX
        console.log('🔧 Step 3: Processing Excel data...');
        const workbook = XLSX.read(new Uint8Array(arrayBuffer), {type: 'array'});
        const modifiedWorkbook = XLSX.utils.book_new();
        
        workbook.SheetNames.forEach((sheetName) => {
            const worksheet = workbook.Sheets[sheetName];
            const jsonData = XLSX.utils.sheet_to_json(worksheet, {header: 1});
            
            const replacements = {
                'P1': document.getElementById('p1')?.value?.trim() || null,
                'L1': document.getElementById('l1')?.value?.trim() || null,
                'L2': document.getElementById('l2')?.value?.trim() || null,
                'L3': document.getElementById('l3')?.value?.trim() || null,
                'L4': document.getElementById('l4')?.value?.trim() || null,
                'L5': document.getElementById('l5')?.value?.trim() || null,
                'VEL': document.getElementById('vel')?.value?.trim() || null,
                'SR': document.getElementById('sr')?.value?.trim() || null,
                'IA': document.getElementById('ia')?.value?.trim() || null
            };

            const newSheet = jsonData.map((row, rowIndex) => {
                if (!Array.isArray(row)) return row;
                
                const originalPValues = [];
                const originalLValues = [];
                
                const modifiedRow = row.map(cell => {
                    if (!cell) return cell;
                    const cellStr = String(cell).trim();
                    
                    if (cellStr.match(/^P[1-3]$/) || cellStr.toLowerCase() === 'ipref') {
                        originalPValues.push(cellStr);
                    }
                    
                    if (cellStr.match(/^L[1-5]$/)) {
                        originalLValues.push(cellStr);
                    }
                    
                    if (cellStr.toLowerCase() === 'vel') {
                        return document.getElementById('vel')?.value?.trim() || cell;
                    }
                    
                    if (cellStr === 'IA' || cellStr === '-IA') {
                        const iaValue = parseFloat(document.getElementById('ia')?.value?.trim() || '0');
                        return cellStr.startsWith('-') ? (-Math.abs(iaValue)).toString() : iaValue.toString();
                    }
                    
                    if (cellStr === 'SR' || cellStr === '-SR') {
                        const srValue = parseFloat(document.getElementById('sr')?.value?.trim() || '0');
                        return cellStr.startsWith('-') ? (-Math.abs(srValue)).toString() : srValue.toString();
                    }
                    
                    if (cellStr.toLowerCase() === 'p1' || cellStr.toLowerCase() === 'ipref') {
                        return document.getElementById('p1')?.value?.trim() || cell;
                    }
                    
                    return replacements[cellStr] || cell;
                });
                
                let lastDataIndex = modifiedRow.length - 1;
                while (lastDataIndex >= 0 && (modifiedRow[lastDataIndex] === null || modifiedRow[lastDataIndex] === undefined || modifiedRow[lastDataIndex] === '')) {
                    lastDataIndex--;
                }
                
                const extendedRow = [...modifiedRow];
                while (extendedRow.length <= lastDataIndex + 2) {
                    extendedRow.push('');
                }
                
                if (rowIndex === 0) {
                    extendedRow[lastDataIndex + 1] = 'Original P Values';
                    extendedRow[lastDataIndex + 2] = 'Original L Values';
                } else {
                    extendedRow[lastDataIndex + 1] = originalPValues.join(', ');
                    extendedRow[lastDataIndex + 2] = originalLValues.join(', ');
                }
                
                return extendedRow;
            });

            const modifiedWorksheet = XLSX.utils.aoa_to_sheet(newSheet);
            XLSX.utils.book_append_sheet(modifiedWorkbook, modifiedWorksheet, sheetName);
        });

        console.log('✅ Excel data processed');

        // STEP 4: Save modified Excel
        console.log('💾 Step 4: Saving output Excel...');
        const excelBuffer = XLSX.write(modifiedWorkbook, { bookType: 'xlsx', type: 'array' });
        const formData = new FormData();
        formData.append('excelFile', new Blob([excelBuffer]), 'output.xlsx');

        const saveResponse = await fetch('/api/save-excel', {
            method: 'POST',
            body: formData
        });

        const saveData = await saveResponse.json();
        if (!saveData.success) throw new Error(saveData.message);
        console.log('✅ Output Excel saved');

        //  STEP 5: Read back and extract data
        console.log('📤 Step 5: Extracting data for database...');
        const outputResponse = await fetch('/api/read-output-excel');
        const outputBuffer = await outputResponse.arrayBuffer();
        const outputWorkbook = XLSX.read(new Uint8Array(outputBuffer), {type: 'array'});
        
        const extractedData = [];

        outputWorkbook.SheetNames.forEach((sheetName) => {
            const worksheet = outputWorkbook.Sheets[sheetName];
            const jsonData = XLSX.utils.sheet_to_json(worksheet, {header: 1});
            
            let headerRowIndex = jsonData.findIndex(row => 
                row && Array.isArray(row) && row.includes('No of Tests')
            );
            
            if (headerRowIndex === -1) {
                throw new Error('Invalid Excel format: Missing required headers');
            }
            
            // ...existing code...
            const headerRow = jsonData[headerRowIndex];

            // Helper: try multiple possible header names, return first match or -1
            function findHeaderIndex(possibleNames) {
                if (!Array.isArray(possibleNames)) possibleNames = [possibleNames];
                for (const nm of possibleNames) {
                    const idx = headerRow.findIndex(h => {
                        if (h == null) return false;
                        return String(h).trim().toLowerCase() === String(nm).trim().toLowerCase();
                    });
                    if (idx !== -1) return idx;
                }
                return -1;
            }

            // Try common variants for each column (be forgiving if excel changed)
            const columns = {
                runs: findHeaderIndex(['No of Tests', 'No. of Tests', 'Number of Tests', 'No of Test', 'No of tests']),
                testName: findHeaderIndex(['Test Name','TestName','Test']),
                pressure: findHeaderIndex(['Inflation Pressure [bar]','Inflation pressure [bar]','Inflation Pressure']),
                velocity: findHeaderIndex(['Velocity [km/h]','Velocity [km/h]','Velocity','velocity','VEL']),
                preload: findHeaderIndex(['Preload [N]','Preload [N]','Preload','preload']),
                camber: findHeaderIndex(['Camber [Deg]','Camber [deg]','Camber']),
                slipAngle: findHeaderIndex(['Slip Angle [deg]','Slip Angle [deg]','Slip Angle']),
                displacement: findHeaderIndex(['Displacement [mm]','Displacement [mm]','Displacement','disp']),
                slipRange: findHeaderIndex(['Slip range [%]','Slip Range [%]','Slip range','Slip range']),
                cleat: findHeaderIndex(['Cleat','Cleat Type','cleat']),
                roadSurface: findHeaderIndex(['Road Surface','Road surface']),
                job: findHeaderIndex(['Job','job','JOB']),
                old_job: findHeaderIndex(['Old Job','old_job','old job','OLD_JOB']),
                template_tydex: findHeaderIndex(['Template Tydex','Template_Tydex','Template Tydex']),
                tydex_name: findHeaderIndex(['Tydex name','tydex_name','Tydex Name','TYDEX_NAME'])
            };

            // Determine p and l columns (most files place P and L after tydex_name)
            let pColumnIndex = -1;
            let lColumnIndex = -1;
            if (columns.tydex_name >= 0) {
                pColumnIndex = columns.tydex_name + 1;
                lColumnIndex = columns.tydex_name + 2;
            } else {
                // fallback: try find headers 'P' and 'L' (case-insensitive)
                pColumnIndex = headerRow.findIndex(h => h && String(h).trim().toLowerCase() === 'p');
                lColumnIndex = headerRow.findIndex(h => h && String(h).trim().toLowerCase() === 'l');
                // final fallback: last two columns
                if (pColumnIndex === -1 || lColumnIndex === -1) {
                    pColumnIndex = Math.max(0, headerRow.length - 2);
                    lColumnIndex = Math.max(0, headerRow.length - 1);
                    console.warn('Fallback: using last two columns for P and L indices', pColumnIndex, lColumnIndex);
                }
            }

            // Required minimal columns
            const strictlyRequired = ['runs', 'testName', 'job']; // keep these strict
            const missingStrict = strictlyRequired.filter(k => columns[k] === -1);

            if (missingStrict.length > 0) {
                throw new Error('Invalid Excel format: Missing required headers: ' + missingStrict.join(', '));
            }

            // Optional columns that may be missing in new simplified CDTire excel
            const optionalCols = ['velocity','preload','displacement','pressure','camber','slipAngle','slipRange','cleat','roadSurface','old_job','template_tydex','tydex_name'];

            const missingOptional = optionalCols.filter(k => columns[k] === -1);
            if (missingOptional.length > 0) {
                console.warn('Some optional CDTire columns missing from Excel — will continue with empty/default values:', missingOptional.join(', '));
            }

            // Now extract rows safely: use index >=0 checks and fallback to ''
            for (let i = headerRowIndex + 1; i < jsonData.length; i++) {
                const row = jsonData[i];
                if (!row || !row[columns.runs]) continue;

                const getCell = (idx) => {
                    try {
                        if (idx >= 0 && Array.isArray(row) && idx < row.length) {
                            return row[idx] == null ? '' : String(row[idx]).trim();
                        }
                    } catch (e) { /* ignore */ }
                    return '';
                };

                const cleanValue = (val) => (val == null) ? '' : String(val).trim().replace(/\n/g, ' ');

                extractedData.push({
                    number_of_runs: parseInt(getCell(columns.runs)) || 0,
                    test_name: cleanValue(getCell(columns.testName)),
                    inflation_pressure: cleanValue(getCell(columns.pressure)),
                    velocity: cleanValue(getCell(columns.velocity)),
                    preload: cleanValue(getCell(columns.preload)),
                    camber: cleanValue(getCell(columns.camber)),
                    slip_angle: cleanValue(getCell(columns.slipAngle)),
                    displacement: cleanValue(getCell(columns.displacement)),
                    slip_range: cleanValue(getCell(columns.slipRange)),
                    cleat: cleanValue(getCell(columns.cleat)),
                    road_surface: cleanValue(getCell(columns.roadSurface)),
                    job: cleanValue(getCell(columns.job)),
                    old_job: cleanValue(getCell(columns.old_job)),
                    template_tydex: cleanValue(getCell(columns.template_tydex)),
                    tydex_name: cleanValue(getCell(columns.tydex_name)),
                    p: cleanValue(getCell(pColumnIndex)),
                    l: cleanValue(getCell(lColumnIndex))
                });
            }
// ...existing code...
        });

        if (extractedData.length === 0) {
            throw new Error('No valid data found in Excel file');
        }

        console.log(`✅ Extracted ${extractedData.length} rows`);

        //  STEP 6: Store in database
        console.log('💾 Step 6: Storing data in database...');
        const storeResponse = await fetch('/api/store-cdtire-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: extractedData })
        });

        const storeData = await storeResponse.json();
        if (!storeData.success) throw new Error(storeData.message);
        console.log('✅ Data stored in database');
        
        //  STEP 7: Create protocol folders
        console.log('📁 Step 7: Creating protocol folders...');
        const projectName = sessionStorage.getItem('currentProject') || 'DefaultProject';
        const folderResponse = await fetch('/api/create-protocol-folders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                projectName: projectName,
                protocol: 'CDTire'
            })
        });

        const folderData = await folderResponse.json();
        if (!folderData.success) {
            throw new Error(folderData.message || 'Error creating protocol folders');
        }

        // Replace lines 680-690 with:

        console.log('✅ Protocol folders created');
        
        // ✅ STEP 8: Save matrix to permanent project table
        console.log('💾 Step 8: Saving matrix to project table...');
        const pid = getProjectId();
        if (pid) {
            const matrixResponse = await fetch('/api/store-project-matrix', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ projectId: pid, protocol: 'CDTire' })
            });
            
            const matrixData = await matrixResponse.json();
            if (!matrixData.success) {
                console.warn('Failed to save matrix:', matrixData.message);
            } else {
                console.log('✅ Matrix saved to project table');
            }
        }
        
        // ✅ STEP 9: REDIRECT TO SELECT PAGE
        console.log('🎉 All steps complete - redirecting to select.html');
        
        // Add project ID to URL for select page
        const projectId = sessionStorage.getItem('currentProjectId');
        const redirectUrl = projectId ? `/select.html?projectId=${projectId}` : '/select.html';
        
        // ✅ Small delay to ensure all async operations complete
        setTimeout(() => {
            console.log('🔄 Redirecting to:', redirectUrl);
            window.location.href = redirectUrl;
        }, 300);
        
        return; // ✅ Stop execution here
        
    } catch (error) {
        console.error('❌ Error in processCDTireExcel:', error);
        console.error('Stack trace:', error.stack);
        errorMessage.style.color = '#d9534f';
        errorMessage.style.display = 'block';
        errorMessage.textContent = error.message || 'Error processing file. Please try again.';
        throw error;
    }
}

// ==== shared helpers ====
function getProjectId() {
  const qs = new URLSearchParams(location.search);
  return qs.get('projectId');
}
async function fetchProject(id) {
  const r = await fetch(`/api/projects/${id}`);
  if (!r.ok) throw new Error('Failed to fetch project');
  return r.json();
}
async function saveInputs(projectId, inputs) {
  await fetch(`/api/projects/${projectId}/inputs`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inputs })
  });
}
// set input values by element id
function prefill(inputs) {
  if (!inputs) return;
  Object.keys(inputs).forEach(key => {
    const el = document.getElementById(key);
    if (el) el.value = inputs[key];
  });
}
// collect values for the ids that actually exist on this page

function collectInputs(ids) {
  const out = {};
  
  if (!Array.isArray(ids)) {
    console.warn('collectInputs: ids is not an array', ids);
    return out;
  }
  
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el && el.value && el.value.trim() !== '') {
      out[id] = el.value.trim();
    }
  });
  
  return out;
}
// ====

// Replace lines 564-620 with:

document.addEventListener('DOMContentLoaded', async () => {
  console.log('🔄 CDTire page loaded');
  
  const pid = getProjectId();
  if (!pid) {
    console.log('ℹ️ No project ID found - fresh page load');
    return;
  }

  console.log('🔍 Loading saved inputs for project:', pid);
  
  try {
    const proj = await fetchProject(pid);
    
    if (!proj || !proj.project) {
      console.warn('⚠️ No project data found');
      return;
    }
    
    const savedInputs = proj.project.inputs;
    
    if (!savedInputs || typeof savedInputs !== 'object') {
      console.log('ℹ️ No saved inputs found');
      return;
    }

    console.log('📥 Saved inputs:', savedInputs);
    
    //  STEP 1: Restore mandatory fields first
    const mandatoryFields = ['rimWidth', 'rimDiameter', 'p1', 'l1'];
    mandatoryFields.forEach(id => {
      if (savedInputs[id]) {
        const el = document.getElementById(id);
        if (el) {
          el.value = savedInputs[id];
          console.log(`✅ Restored ${id}:`, savedInputs[id]);
        }
      }
    });
    
    //  STEP 2: Restore optional parameters that were saved
    const optionalFieldMap = {
      'nominalWidth': 'nominalWidth',
      'outerDiameter': 'outerDiameter',
      'l2': 'l2',
      'l3': 'l3',
      'l4': 'l4',
      'l5': 'l5',
      'vel': 'vel',
      'ia': 'ia',
      'sr': 'sr',
      'aspectRatio': 'aspectRatio'
    };
    
    // Wait for DOM to be fully ready
    setTimeout(() => {
      Object.keys(optionalFieldMap).forEach(paramKey => {
        const inputId = optionalFieldMap[paramKey];
        
        // Check if this field has a saved value
        if (savedInputs[inputId] && savedInputs[inputId] !== '') {
          console.log(`🔧 Restoring optional parameter: ${paramKey} = ${savedInputs[inputId]}`);
          
          // Add the parameter to the form if not already added
          if (!addedParams.has(paramKey)) {
            addParameter(paramKey);
            console.log(`➕ Added parameter: ${paramKey}`);
          }
          
          // Set the value after a short delay to ensure DOM is updated
          setTimeout(() => {
            const el = document.getElementById(inputId);
            if (el) {
              el.value = savedInputs[inputId];
              console.log(`✅ Set value for ${inputId}:`, savedInputs[inputId]);
            } else {
              console.warn(`⚠️ Element not found: ${inputId}`);
            }
          }, 150);
        }
      });
    }, 100);
    
    console.log('✅ Input restoration complete');
    
  } catch (e) { 
    console.error('❌ Failed to restore saved inputs:', e);
  }
});