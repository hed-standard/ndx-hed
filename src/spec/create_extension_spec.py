# -*- coding: utf-8 -*-
import os.path

from pynwb.spec import NWBNamespaceBuilder, export_spec, NWBDatasetSpec, NWBGroupSpec, NWBAttributeSpec

# TODO: import other spec classes as needed
# from pynwb.spec import , NWBLinkSpec, NWBDtypeSpec, NWBRefSpec


def main():
    # these arguments were auto-generated from your cookiecutter inputs
    ns_builder = NWBNamespaceBuilder(
        name="""ndx-hed""",
        version="""0.1.0""",
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
    ns_builder.include_type('LabMetaData', namespace='core')
    ns_builder.include_type('VectorData', namespace='core')

    hed_tags = NWBDatasetSpec(
        neurodata_type_def="HedTags",
        neurodata_type_inc="VectorData",
        doc=("An extension of VectorData for Hierarchical Event Descriptor (HED) tags. If HED tags are used, "
             "the HED schema version must be specified in the NWB file using the HedMetadata type."),
        dtype="text",
    )

    hed_version_attr = NWBGroupSpec(
        name="hed_version",  # fixed name
        neurodata_type_def="HedVersionAttr",
        neurodata_type_inc="LabMetaData",
        doc=("An extension of LabMetaData to store the Hierarchical Event Descriptor (HED) schema version. "
             "TODO When merged with core, "
             "this will no longer inherit from LabMetaData but from NWBContainer and be placed "
             "optionally in /general."),
        attributes=[
            NWBAttributeSpec(
                name="version",
                doc=(
                    "The version of the HED schema used to validate the HED tags, e.g., '8.2.0'. "
                    "Required if HED tags are used in the NWB file."
                ),
                dtype='text',
                required=True
                #shape=[None,]
            )
        ]
    )
    
    hed_version = NWBGroupSpec(
        name="hed_version",  # fixed name
        neurodata_type_def="HedVersion",
        neurodata_type_inc="LabMetaData",
        doc=("An extension of LabMetaData to store the Hierarchical Event Descriptor (HED) schema version. "
             "TODO When merged with core, "
             "this will no longer inherit from LabMetaData but from NWBContainer and be placed "
             "optionally in /general."),
    )

    hed_version.add_dataset(
            name="version",
            doc="HED schema version to use for this dataset",
            dtype='text',
            quantity='?'
    )
    
    # TODO: add all of your new data types to this list
    new_data_types = [hed_version_attr, hed_tags, hed_version]

    # export the spec to yaml files in the spec folder
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "spec"))
    export_spec(ns_builder, new_data_types, output_dir)
    print("Spec files generated. Please make sure to run `pip install .` to load the changes.")


if __name__ == "__main__":
    # usage: python create_extension_spec.py
    main()