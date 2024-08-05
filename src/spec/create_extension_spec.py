# -*- coding: utf-8 -*-
import os.path

from pynwb.spec import NWBNamespaceBuilder, export_spec, NWBDatasetSpec, NWBAttributeSpec


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
    ns_builder.include_type('VectorData', namespace='core')

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
                    "The version of the HED schema used to validate the HED tags, e.g., '8.2.0'. (Required). "
                ),
                dtype='text',
                required=True
            )
        ]
    )

    # TODO: add all of your new data types to this list
    #new_data_types = [hed_version_attr, hed_tags, hed_version]
    new_data_types = [hed_tags]

    # export the spec to yaml files in the spec folder
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "spec"))
    export_spec(ns_builder, new_data_types, output_dir)
    print("Spec files generated. Please make sure to run `pip install .` to load the changes.")


if __name__ == "__main__":
    # usage: python create_extension_spec.py
    main()
