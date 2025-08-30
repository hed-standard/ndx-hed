# -*- coding: utf-8 -*-
import os.path

from pynwb.spec import NWBNamespaceBuilder, export_spec, NWBDatasetSpec, NWBAttributeSpec, NWBGroupSpec


def main():
    # these arguments were auto-generated from your cookiecutter inputs
    ns_builder = NWBNamespaceBuilder(
        name="""ndx-hed""",
        version="""0.2.0""",
        doc="""NWB extension for HED data""",
        author=[
            "Ryan Ly",
            "Oliver Ruebel",
            "Kay Robbins",
            "Ian Callanan",
        ],
        contact=[
            "rly@lbl.gov",
            "oruebel@lbl.gov",
            "kay.robbins@utsa.edu",
            "ianrcallanan@gmail.com",
        ],
    )

    ns_builder.include_namespace("core")
    ns_builder.include_type('VectorData', namespace='core')
    ns_builder.include_type('LabMetaData', namespace='core')

    hed_tags = NWBDatasetSpec(
        neurodata_type_def="HedTags",
        neurodata_type_inc="VectorData",
        doc=("An extension of VectorData for Hierarchical Event Descriptor (HED) tags. If HED tags are used, "
             "the HED schema version must be specified in the NWB file using the HedMetadata type."),
        dtype="text",
        attributes=[
            NWBAttributeSpec(
                name="hed_version",
                doc=(
                    "The version of the HED schema used to validate the HED tags, e.g., '8.4.0'. (Required). "
                ),
                dtype='text',
                required=True
            )
        ]
    )

    # Define our LabMetaData type
    hed_lab_metadata = NWBGroupSpec(
        neurodata_type_def='HedLabMetaData',
        neurodata_type_inc='LabMetaData',
        doc='Extension type for storing a HED (Hierarchical Event Descriptor) schema in lab metadata',
        attributes=[
            NWBAttributeSpec(
                name='hed_schema_version',
                doc="The HED schema version used in this NWB file, e.g., '8.4.0'.",
                dtype='text',
                required=True
            )
        ]
    )

    # Add all of new data types to this list
    new_data_types = [hed_lab_metadata, hed_tags]

    # export the spec to yaml files in the spec folder
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'spec'))
    export_spec(ns_builder, new_data_types, output_dir)
    print('Spec files generated. Please make sure to rerun `pip install .` to load the changes.')


if __name__ == "__main__":
    # usage: python create_extension_spec.py
    main()
