import bpy
import math
import xml.etree.ElementTree as ET

# Neteja l'escena abans de començar
if bpy.ops.object.select_all.poll():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)

def note_number(note, octave):
    base_notes = {'A': 1, 'B': 3, 'C': -8, 'D': -6, 'E': -4, 'F': -3, 'G': -1}
    note_val = base_notes.get(note, 0)
    note_val += octave * 12
    return note_val

def get_harmonics(note_val, count=10):
    harmonics = []
    fundamental_freq = 440 * math.pow(2.0, (note_val - 49) / 12.0)
    
    for i in range(1, count + 1):
        harmonic_freq = fundamental_freq * i
        harmonic_note = int(round(12 * math.log2(harmonic_freq / 440) + 49))
        harmonics.append(harmonic_note)
        
    return set(harmonics)

def get_or_create_voice_material(voice):
    mat_name = f"Color_Voice_{voice}"
    
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    else:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = False
        
        if voice == 1: # Blau
            mat.diffuse_color = (0.1, 0.1, 1.0, 1.0) 
        elif voice == 2: # Verd
            mat.diffuse_color = (0.1, 1.0, 0.1, 1.0)
        elif voice == 3: # Vermell
            mat.diffuse_color = (1.0, 0.1, 0.1, 1.0)
        elif voice == 4: # Lila
            mat.diffuse_color = (0.8, 0.1, 0.8, 1.0) 
        elif voice == 5: # Blanc
            mat.diffuse_color = (1.0, 1.0, 1.0, 1.0)
        else: # Gris
            mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
        
        return mat

def create_point(location, voice, name="Point"):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=location)
    cube = bpy.context.active_object
    cube.name = name
    
    mat = get_or_create_voice_material(voice)
    
    if cube.data.materials:
        cube.data.materials[0] = mat
    else:
        cube.data.materials.append(mat)
    
    return cube

def create_bezier_curves(voice_data):
    for voice_num, points in voice_data.items():
        if len(points) < 2:
            continue
            
        curve_data = bpy.data.curves.new(f'VoiceCurveData_{voice_num}', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.fill_mode = 'FULL'
        curve_data.bevel_depth = 0.05
        
        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(len(points) - 1)
        
        for i, point_coord in enumerate(points):
            bp = spline.bezier_points[i]
            bp.co = point_coord
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'
        
        curve_obj = bpy.data.objects.new(f'Voice_{voice_num}_Curve', curve_data)
        
        mat = get_or_create_voice_material(voice_num)
        curve_obj.data.materials.append(mat)
        
        bpy.context.collection.objects.link(curve_obj)


def read_xml_and_translate(input_file):
    print(f"Processant fitxer: {input_file}")
    
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
        
        # Paràmetres per al cercle
        radius = 5.0
        
        scale_z = 0.2
        x_offset, divisions = 0.0, 1.0
        time_signature = {'beats': 4, 'beat-type': 4}

        color_to_voice = {'#0000FF': 1, '#00AA00': 2, '#FF0000': 3, '#AA00FF': 4}
        
        voice_points = {1: [], 2: [], 3: [], 4: [], 5: []}
        
        notes_at_time = {}
        
        
        total_duration = 0.0
        for part in root.findall('part'):
            for measure in part.findall('measure'):
                for element in measure:
                    if element.tag == 'note':
                        duration_elem = element.find('duration')
                        if duration_elem is not None: total_duration += float(duration_elem.text)
                    elif element.tag == 'backup':
                        duration_elem = element.find('duration')
                        if duration_elem is not None: total_duration -= float(duration_elem.text)

        # Recorregut per crear els punts en forma de cercle
        x_offset = 0.0
        for part in root.findall('part'):
            for measure in part.findall('measure'):
                measure_num = measure.get('number')
                
                measure_time_cursor = 0.0
                
                for element in measure:
                    if element.tag == 'attributes':
                        div_elem = element.find('divisions')
                        if div_elem is not None: divisions = float(div_elem.text)
                        
                        time_elem = element.find('time')
                        if time_elem is not None:
                            beats = time_elem.find('beats')
                            beat_type = time_elem.find('beat-type')
                            if beats is not None and beat_type is not None:
                                time_signature = {'beats': int(beats.text), 'beat-type': int(beat_type.text)}

                    elif element.tag == 'note':
                        color_hex, voice_num = None, None
                        if 'color' in element.attrib: color_hex = element.get('color')
                        else:
                            notehead = element.find('notehead')
                            if notehead is not None and 'color' in notehead.attrib:
                                color_hex = notehead.get('color')
                        
                        if color_hex: voice_num = color_to_voice.get(color_hex.upper())
                        
                        if element.find('rest') is None and voice_num is not None:
                            pitch = element.find('pitch')
                            if pitch is not None:
                                step = pitch.find('step').text
                                octave = int(pitch.find('octave').text)
                                alter_elem = pitch.find('alter')
                                
                                note_val = note_number(step, octave)
                                if alter_elem is not None: note_val += int(alter_elem.text)
                                
                                current_time = round((x_offset + measure_time_cursor), 2)
                                if current_time not in notes_at_time:
                                    notes_at_time[current_time] = {}
                                notes_at_time[current_time][voice_num] = note_val
                                
                                # Càlcul de coordenades circulars
                                angle = (current_time / total_duration) * 2 * math.pi
                                
                                # Coordenades amb radi constant
                                x_location = radius * math.cos(angle)
                                y_location = radius * math.sin(angle)
                                z_location = note_val * scale_z
                                
                                location = (x_location, y_location, z_location)
                                
                                voice_points[voice_num].append(location)
                                create_point(location, voice_num, f"M{measure_num}_V{voice_num}")

                        duration_elem = element.find('duration')
                        if duration_elem is not None: measure_time_cursor += float(duration_elem.text)
                    
                    elif element.tag == 'backup':
                        duration_elem = element.find('duration')
                        if duration_elem is not None: measure_time_cursor -= float(duration_elem.text)
            
                measure_duration = (time_signature['beats'] * (4.0 / time_signature['beat-type'])) * divisions
                x_offset += measure_duration
        
        # Càlcul de la cinquena veu (harmònics conjunts)
        for time_point, voices in notes_at_time.items():
            if len(voices) < 2:
                num_shared_harmonics = 0
            else:
                harmonic_sets = [get_harmonics(note_val, count=10) for note_val in voices.values()]
                common_harmonics = set.intersection(*harmonic_sets)
                num_shared_harmonics = len(common_harmonics)
            
            angle = (time_point / total_duration) * 2 * math.pi
            
            # Coordenades amb radi constant
            x_location = radius * math.cos(angle)
            y_location = radius * math.sin(angle)
            z_location = num_shared_harmonics * scale_z
            
            location_5 = (x_location, y_location, z_location)
            
            voice_points[5].append(location_5)
            create_point(location_5, 5, f"SharedHarmonics_T{time_point}")
        
        create_bezier_curves(voice_points)

    except Exception as e:
        print(f"S'ha produït un error inesperat: {str(e)}")


input_file = "C:\\Users\\EricdelRíoSanz\\Desktop\\TdR\\Fuga_16_colors.musicxml"
read_xml_and_translate(input_file)