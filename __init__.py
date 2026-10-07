import bpy
import bmesh
from itertools import groupby
from operator import itemgetter
from mathutils import kdtree

bl_info = {
    "name": "Selection Info",
    "author": "coldrifting",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "category": "3D View",
}


def ints_to_ranges(ints) -> str:
    # Sort the list and remove duplicates if necessary
    sorted_ints = sorted(set(ints))
    ranges = []
    # group items based on the difference between the value and its index
    for k, g in groupby(enumerate(sorted_ints), lambda ix: ix[0] - ix[1]):
        group = list(map(itemgetter(1), g))
        if len(group) == 1:
            ranges.append(f"{group[0]}")
        else:
            ranges.append(f"{group[0]}-{group[-1]}")
    return ", ".join(ranges)


def get_vertices() -> str:
    obj = bpy.context.edit_object
    if obj is not None and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        selected_vertices = [vertex.index for vertex in bm.verts if vertex.select]
        return ints_to_ranges(selected_vertices)

    return ""

def get_vertex_positions() -> str:
    positions = {}
    max_size = -1
    output = ""

    obj = bpy.context.edit_object
    if obj is not None and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        vertex_indices = [vertex.index for vertex in bm.verts if vertex.select]

        bm.normal_update()

        for index in vertex_indices:
            positions[index] = bm.verts[index].co
            if index > max_size:
                max_size = index

    for index, uv in positions.items():
        index_str = (str(index) + ":").ljust(len(str(max_size)) + 1)
        x = "x: " + f"{uv.x:08.6f}".rjust(9)
        y = "y: " + f"{uv.y:08.6f}".rjust(9)
        z = "z: " + f"{uv.z:08.6f}".rjust(9)

        output += f"{index_str} {{{x}, {y}, {z}}}\n"

    return output

def get_vertex_normals() -> str:
    normals = {}
    max_size = -1
    output = ""

    obj = bpy.context.edit_object
    if obj is not None and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        vertex_indices = [vertex.index for vertex in bm.verts if vertex.select]

        bm.normal_update()

        for index in vertex_indices:
            normals[index] = bm.verts[index].normal
            if index > max_size:
                max_size = index

    for index, uv in normals.items():
        index_str = (str(index) + ":").ljust(len(str(max_size)) + 1)
        x = "x: " + f"{uv.x:08.6f}".rjust(9)
        y = "y: " + f"{uv.y:08.6f}".rjust(9)
        z = "z: " + f"{uv.z:08.6f}".rjust(9)

        output += f"{index_str} {{{x}, {y}, {z}}}\n"

    return output


def get_vertex_uvs() -> str:
    output = ""
    uvs = {}
    obj = bpy.context.edit_object
    max_size = -1
    if obj is not None and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        vertex_indices = [vertex.index for vertex in bm.verts if vertex.select]
        for index in vertex_indices:
            if index > max_size:
                max_size = index

        vertex_indices = sorted(list(vertex_indices))

        uv_layer = bm.loops.layers.uv.active

        for index in vertex_indices:
            for loop in bm.verts[index].link_loops:
                uvs[index] = loop[uv_layer].uv
                break

        for index, uv in uvs.items():
            index_str = (str(index) + ":").ljust(len(str(max_size)) + 1)
            x = "x: " + f"{uv.x:08.6f}".rjust(9)
            y = "y: " + f"{uv.y:08.6f}".rjust(9)

            output += f"{index_str} {{{x}, {y}}}\n"

    return output


def get_overlapping_vertex_pairs():
    obj = bpy.context.edit_object
    if obj is not None and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        selected_vertices = [vertex.index for vertex in bm.verts if vertex.select]

        dist = 0.01
        size = len(bm.verts)

        kd = kdtree.KDTree(size)
        for i, v in enumerate(bm.verts):
            kd.insert(v.co, i)
        kd.balance()

        visited = set()
        overlapping_groups = []
        for i, v in enumerate(bm.verts):
            if i in visited:
                continue
            # Find all vertices within the threshold distance
            # Returns a list of tuples: (co, index, dist)
            co_find = kd.find_range(v.co, dist)
            # If more than 1 vertex is found, they are overlapping
            if len(co_find) > 1:
                group = [index for co, index, dist in co_find]
                overlapping_groups.append(group)
                # Mark all vertices in this group as visited so we don't duplicate groups
                visited.update(group)
            else:
                visited.add(i)

        for i in reversed(range(len(overlapping_groups))):
            for j in reversed(range(len(overlapping_groups[i]))):
                if overlapping_groups[i][j] not in selected_vertices:
                    del overlapping_groups[i][j]

        for i in reversed(range(len(overlapping_groups))):
            if len(overlapping_groups[i]) < 2:
                del overlapping_groups[i]

        return "- " + str(overlapping_groups)[1:-1].replace("], [", "]\n- [")

    return ""

def get_face_indices() -> str:
    obj = bpy.context.edit_object
    if obj is not None and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        selected_faces = [face.index for face in bm.faces if face.select]
        return ints_to_ranges(selected_faces)

    return ""


def get_face_uvs() -> str:
    output = ""
    uvs = {}
    obj = bpy.context.edit_object
    max_size = -1
    if obj is not None and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        selected_faces = [f for f in bm.faces if f.select]
        vertex_indices = set()

        for face in selected_faces:
            for vert in face.verts:
                vertex_indices.add(vert.index)
                if vert.index > max_size:
                    max_size = vert.index

        vertex_indices = sorted(list(vertex_indices))

        uv_layer = bm.loops.layers.uv.active

        for index in vertex_indices:
            for loop in bm.verts[index].link_loops:
                uvs[index] = loop[uv_layer].uv
                break

        for index, uv in uvs.items():
            index_str = (str(index) + ":").ljust(len(str(max_size)) + 1)
            x = "x: " + f"{uv.x:08.6f}".rjust(9)
            y = "y: " + f"{uv.y:08.6f}".rjust(9)

            output += f"{index_str} {{{x}, {y}}}\n"

    return output


class SelectionInfoPanel_GetVertexIndices(bpy.types.Operator):
    bl_idname = "selection_info_panel.get_vertex_indices"
    bl_label = "Copy Indices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Call your function inside the execute method
        output = get_vertices()
        bpy.context.window_manager.clipboard = output

        # Show a small pop-up notification in Blender's status bar
        self.report({'INFO'}, "Selected vertex indices copied to clipboard")
        return {'FINISHED'}


class SelectionInfoPanel_GetVertexPositions(bpy.types.Operator):
    bl_idname = "selection_info_panel.get_vertex_positions"
    bl_label = "Copy Positions"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        output = get_vertex_positions()
        bpy.context.window_manager.clipboard = output

        self.report({'INFO'}, "Selected vertex positions copied to clipboard")
        return {'FINISHED'}


class SelectionInfoPanel_GetVertexNormals(bpy.types.Operator):
    bl_idname = "selection_info_panel.get_vertex_normals"
    bl_label = "Copy Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        output = get_vertex_normals()
        bpy.context.window_manager.clipboard = output

        self.report({'INFO'}, "Selected vertex normals copied to clipboard")
        return {'FINISHED'}


class SelectionInfoPanel_GetVertexUVs(bpy.types.Operator):
    bl_idname = "selection_info_panel.get_vertex_uvs"
    bl_label = "Copy UVs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        output = get_vertex_uvs()
        bpy.context.window_manager.clipboard = output

        self.report({'INFO'}, "Selected vertex UVs copied to clipboard")
        return {'FINISHED'}


class SelectionInfoPanel_GetVertexOverlappingPairs(bpy.types.Operator):
    bl_idname = "selection_info_panel.get_vertex_overlapping_pairs"
    bl_label = "Copy Overlapping"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Call your function inside the execute method
        output = get_overlapping_vertex_pairs()
        bpy.context.window_manager.clipboard = output

        # Show a small pop-up notification in Blender's status bar
        self.report({'INFO'}, "Selected vertex overlapping pairs copied to clipboard")
        return {'FINISHED'}


class SelectionInfoPanel_GetFaceIndices(bpy.types.Operator):
    bl_idname = "selection_info_panel.get_face_indices"
    bl_label = "Copy Indices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Call your function inside the execute method
        output = get_face_indices()
        bpy.context.window_manager.clipboard = output

        # Show a small pop-up notification in Blender's status bar
        self.report({'INFO'}, "Selected face indices copied to clipboard")
        return {'FINISHED'}


class SelectionInfoPanel_GetFaceUvs(bpy.types.Operator):
    bl_idname = "selection_info_panel.get_face_uvs"
    bl_label = "Copy UVs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Call your function inside the execute method
        output = get_face_uvs()
        bpy.context.window_manager.clipboard = output

        # Show a small pop-up notification in Blender's status bar
        self.report({'INFO'}, "Selected face UVs copied to clipboard")
        return {'FINISHED'}


class SelectionInfoPanel(bpy.types.Panel):
    bl_idname = "selection_info_panel"
    bl_label = "Selection Info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MODE' or (context.object and context.object.mode == 'EDIT'):
            obj = bpy.context.edit_object
            if obj is not None and obj.type == 'MESH':
                select_mode = bpy.context.tool_settings.mesh_select_mode
                if select_mode[0] or select_mode[2]:
                    bm = bmesh.from_edit_mesh(obj.data)
                    selected_vertices = [vertex for vertex in bm.verts if vertex.select]
                    return len(selected_vertices) > 0

        return False

    def draw(self, context):
        obj = bpy.context.edit_object
        if obj is not None and obj.type == 'MESH':
            select_mode = bpy.context.tool_settings.mesh_select_mode
            bm = bmesh.from_edit_mesh(obj.data)
            # Vertices
            if select_mode[0]:
                self.layout.label(text="Vertices")
                self.layout.operator("selection_info_panel.get_vertex_indices")
                self.layout.operator("selection_info_panel.get_vertex_positions")
                self.layout.operator("selection_info_panel.get_vertex_normals")
                self.layout.operator("selection_info_panel.get_vertex_uvs")
                self.layout.operator("selection_info_panel.get_vertex_overlapping_pairs")

            # Faces
            elif select_mode[2]:
                selected_faces = [face.index for face in bm.faces if face.select]
                if len(selected_faces) > 0:
                    self.layout.label(text="Faces")
                    self.layout.operator("selection_info_panel.get_face_indices")
                    self.layout.operator("selection_info_panel.get_face_uvs")


def register():
    bpy.utils.register_class(SelectionInfoPanel)
    bpy.utils.register_class(SelectionInfoPanel_GetVertexIndices)
    bpy.utils.register_class(SelectionInfoPanel_GetVertexPositions)
    bpy.utils.register_class(SelectionInfoPanel_GetVertexNormals)
    bpy.utils.register_class(SelectionInfoPanel_GetVertexUVs)
    bpy.utils.register_class(SelectionInfoPanel_GetVertexOverlappingPairs)

    bpy.utils.register_class(SelectionInfoPanel_GetFaceIndices)
    bpy.utils.register_class(SelectionInfoPanel_GetFaceUvs)


def unregister():
    bpy.utils.unregister_class(SelectionInfoPanel)
    bpy.utils.unregister_class(SelectionInfoPanel_GetVertexIndices)
    bpy.utils.unregister_class(SelectionInfoPanel_GetVertexPositions)
    bpy.utils.unregister_class(SelectionInfoPanel_GetVertexNormals)
    bpy.utils.unregister_class(SelectionInfoPanel_GetVertexUVs)
    bpy.utils.unregister_class(SelectionInfoPanel_GetVertexOverlappingPairs)

    bpy.utils.unregister_class(SelectionInfoPanel_GetFaceIndices)
    bpy.utils.unregister_class(SelectionInfoPanel_GetFaceUvs)
