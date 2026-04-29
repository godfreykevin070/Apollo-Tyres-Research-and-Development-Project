*HEADING
************************************************************************
Project name:
tyre size:
OE:
user:
date:
************************************************************************
*parameter
****load details---------------------
load1_kg=660
load2_kg=555
load3_kg=425
pressure1=24.75
pressure2=32
pressure3=39.25
speed_kmph=80
IA=5
SA=20
SR=30
****RIM_details---------------------
width=178
diameter=487.4
**********-----------------------
Outer_diameter=110
nomwidth=60
aspratio=50
************
inflation_pressure1=0.00689476*pressure1
inflation_pressure1=0.00689476*pressure2
inflation_pressure1=0.00689476*pressure3
load1=9.81*load1_kg
load2=9.81*load2_kg
load3=9.81*load3_kg
Outer_radius=Outer_diameter/2000
speed=speed_kmph*1000*1000/3600
****RIM_Movement---------------------
rimdisp_plus = 60.0
rimdisp_minus = -60.0
*************
initial_velocity=speed/Outer_radius
***********************Cornering*****************
