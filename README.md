# Digital Twin – Safe Stage Rotor Design
> *Implementation of the scientific project funded through a national competition organized by the Ministry of Science and Higher Education.*

## About The Project
This project focused on developing a comprehensive Digital Twin for a safe stage rotor drive system. It was executed at Gdynia Maritime University by the HMI Student Science Club, utilizing funds provided by the Ministry of Science and Higher Education. The scope included designing and assembling the physical electrical installation (along with full documentation), modeling the drive and control system, programming the PLC, and developing an overarching SCADA system. 

By integrating physical hardware with advanced simulations, the project enables real-time synchronization between the mathematical model, industrial controllers, and a 3D physical visualization.

---

## System Components & Technologies
The architecture is distributed across several specialized environments, all communicating synchronously to form the Digital Twin.

* **TIA Portal (PLC Control):** Siemens S7-1200F (CPU 1214FC) programmed in LAD. Handles safety logic, field-oriented control of the asynchronous motor via a frequency converter, and HMI/SCADA data exchange.
* **MATLAB / Simulink:** Mathematical modeling of the drive system, simulating real-world physics, electrical parameters, and mechanical load.
* **Unreal Engine 5:** Provides a real-time, high-fidelity 3D visualization of the physical machine.
* **Python (The Integrator):** The central communication hub bridging all subsystems.

<p align="center">
  <img width="1359" height="566" alt="Topologia_TIA_PORTAL" src="https://github.com/user-attachments/assets/d8692f1a-e560-4767-9753-fcf205c0c735" />

</p>

---

## Core Software Architecture

### 1. Python Data Integrator
A custom Python script acts as the backbone of the Digital Twin. It utilizes asynchronous workers to fetch, process, and route data between MATLAB, TIA Portal, and Unreal Engine without blocking execution. Communication with the MATLAB environment is established via the UDP protocol, while data exchange with the Unreal Engine 3D environment is achieved using the low-latency OSC (Open Sound Control) protocol.

<p align="center">
 <img width="1361" height="604" alt="Python" src="https://github.com/user-attachments/assets/3ed46a10-0946-4145-a70a-223659ab2c4f" />

</p>

### 2. MATLAB / Simulink Drive Model
The Simulink environment accurately mirrors the physical drive system. It simulates the three-phase power grid connected to a SIEMENS G120C frequency converter, which in turn powers a 2.2 kW asynchronous motor.
* **Data Acquisition:** The model continuously measures phase currents ($I_a$, $I_b$).
* **Load Simulation:** A dedicated block calculates the mechanical load (resistance torque) reflecting the characteristics of the stage rotor.
* **Outputs:** The model outputs critical operational data, including angular velocity ($\omega_m$) and angular position ($\theta_m$), which are fed into a Vector Control block parameterized using data from SINAMICS STARTER software.

<p align="center">
  <img width="1400" height="554" alt="Matlab" src="https://github.com/user-attachments/assets/8d412475-79e9-4e3a-92ad-fe4c8499c91c" />

</p>

---

## Unreal Engine 5 Visualization & Simulation
The 3D environment was developed in Unreal Engine 5 to serve dual purposes, adapting to the availability of physical hardware.

### 1. Hardware-in-the-Loop Visualization (Full System)
In the complete hardware setup, Unreal Engine acts as a high-fidelity digital reflection of the physical machine. It visualizes the real-time movement of the stage rotor while displaying live measurements plotted directly from the MATLAB simulation (e.g., angular velocity and angular position).

<p align="center">
  <img width="1916" height="1006" alt="UnrealPhotoTia" src="https://github.com/user-attachments/assets/256b000a-a4fd-4980-99c7-d1e60cf1a852" />

</p>

### 2. Standalone Simulation Mode (Virtual HMI)
To facilitate development, testing, and remote work when the physical PLC and hardware are unavailable, a standalone simulation mode was implemented. In this version, the SCADA/HMI operator panel is embedded directly within the Unreal Engine environment. This allows users to input control parameters (such as target speed, angle, and physical load), control the machine manually or automatically, and observe the simulated physical responses purely in software.

<p align="center">
  <img width="2559" height="1076" alt="UnrealBezTia1" src="https://github.com/user-attachments/assets/77d0d3df-06fc-42ab-9df6-af070d78a798" />
  <img width="2559" height="1079" alt="UnrealBezTia2" src="https://github.com/user-attachments/assets/5aafdd60-6019-4d9c-808d-fd58670616e7" />


</p>

---


## PLC Control Logic & Architecture
The control program running on the Siemens S7-1200F PLC is structured around Function Blocks (FB) called cyclically within the `Main [OB1]` organization block. 

#### 1. System Initialization
Upon boot, the `Startup [OB100]` block ensures the system enters a safe, predictable state. It defaults to Local control, Manual mode, resets speed targets, and checks communication with the inverter and PROFINET devices before allowing any movement.

#### 2. Control Source & Modes
The architecture strictly prevents control conflicts through memory bit interlocking:
* **Remote / Local Selection:** Prioritizes physical control cabinet buttons and the local HMI panel when in Local mode, while allowing SCADA control in Remote mode.
* **Manual / Auto Modes:** Switched via SET/RESET logic. Local operation is restricted to Manual mode for safety, while Remote operation supports both.

#### 3. Movement Execution
In Automatic mode, the operator can command the platform to move:
* **Absolutely:** To a specific target angle (0 – 360°).
* **Relatively:** By a specified angular offset with a defined direction.

#### 4. Speed & Direction Generation
Speed targets are calculated as a percentage of the nominal speed and transmitted to the inverter via the USS protocol (`USS_DRV` block).
* **Manual Mode:** Speed is dictated by sliders on the HMI or SCADA interface.
* **Auto Mode:** Speed is dynamically managed by PI-GS (Gain Scheduling) positioning regulators based on SCADA sequences.
* **Homing:** Safely defaults to 50% nominal speed.

#### 5. Safety Supervision (F-CPU)
Safety is the highest priority. The system continuously monitors the environment and will immediately halt operations upon detecting:
* E-STOP activations from three independent physical locations.
* Frequency inverter faults.
* PROFINET network communication drops.
* Overspeed conditions.
* Position mismatch errors between the two independent encoders.

---

## SCADA Operator Interface (Ignition)
An industrial SCADA system was implemented using the Ignition platform, featuring four dedicated control panels designed for comprehensive stage movement management, data visualization, and monitoring.

### Programming Panel (Panel Programowania)
This panel allows operators to compose motion recipes consisting of sequential movement steps. The compiled instructions are automatically generated and saved in a dedicated directory as JSON files.
<p align="center">
<img width="1435" height="804" alt="PanelProgramowania_Scada" src="https://github.com/user-attachments/assets/27d6358d-ef1b-4e57-97c2-eef2c9eab70e" />
</p>

Example JSON structure:
```json
{
    "Program_name": "program.json", 
    "steps": [
        {
            "step_id": 1, 
            "speed": 10.0, 
            "angle": 10, 
            "direction": "Left"
        } 
    ], 
    "Program_number": "1", 
    "Program_full_name": "1_program.json"
}
```



### Program Execution Panel (Panel Wykonywania Programu)
In this panel, the operator can select a previously created instruction set from the directory and execute the automated program sequence step-by-step, monitoring the progression of the stage sequence in real time.
<p align="center">
<img width="1435" height="804" alt="PanelWykonywaniaProgramu_Scada" src="https://github.com/user-attachments/assets/f7cace89-63bf-4811-b386-0a5ce0005793" />
</p>


### Manual Control Panel (Panel Sterowania Ręcznego)
This interface enables direct manual intervention over the hardware setup. It features a slider to smoothly adjust the stage speed from 0% to 100%, directional buttons to command left or right rotation, and a homing button to return the stage position precisely to 0 degrees.
<p align="center">
<img width="1438" height="806" alt="PanelSterowaniaRęcznego_Scada" src="https://github.com/user-attachments/assets/8e97be6e-79ea-44ad-ac08-0148f9badde2" />
</p>


### Automatic Control Panel (Panel Sterowania Automatycznego)
Dedicated to absolute and relative automatic positioning, this panel allows the operator to input a specific target velocity ranging from 0 to 3.3 RPM and a precise target angle between 0 and 360 degrees for precise automated positioning.
<p align="center">
<img width="1435" height="806" alt="PanelSterowaniaAutomatycznego_Scada" src="https://github.com/user-attachments/assets/30ce7a6f-95a9-4f4b-a139-16ccbc0828b3" />
</p>


---


## Final Project Showcase
Below are the photographs and visual results of the fully assembled and integrated physical setup working in tandem with its Digital Twin.



<p align="center">
 <img width="4066" height="3050" alt="IMG_1747" src="https://github.com/user-attachments/assets/a7108855-4959-4527-a343-00cdcc9456a3" />
<img width="4284" height="5712" alt="IMG_1731" src="https://github.com/user-attachments/assets/4ad09c5e-3c6f-41ff-81fe-62b6c53076bb" />


https://github.com/user-attachments/assets/79c351df-109b-49e4-b986-bbf676ce093a

</p>


For a better quality photos and videos, here is my google drive link
https://drive.google.com/drive/folders/10J8Htn7ib1zHesmU3C8aU7uZpWQstneW?usp=sharing

---

## The Team
 
* **Piotr Wieleba**: 
* **Mateusz Zych**: 
* **Paweł Jędryczka**:
* **Jakub Lidzbarski**:
* **Bartosz Korycki**:
* **Kamil Kaczmarek**:
* **Artur Zakacz**:
