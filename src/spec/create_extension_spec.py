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
    ns_builder.include_type("VectorData", namespace="core")
    ns_builder.include_type("LabMetaData", namespace="core")

    hed_tags = NWBDatasetSpec(
        neurodata_type_def="HedTags",
        neurodata_type_inc="VectorData",
        doc="An extension of VectorData for Hierarchical Event Descriptor (HED) tags. Always has the name HED",
        dtype="text",
    )

    hed_value_vector = NWBDatasetSpec(
        neurodata_type_def="HedValueVector",
        neurodata_type_inc="VectorData",
        doc="An extension of VectorData for Hierarchical Event Descriptor (HED) tags. Always has the name HED",
        attributes=[
            NWBAttributeSpec(
                name="hed", dtype="text", doc="The HED annotation applicable to the column (expects #).", required=True
            )
        ],
    )

    # Define our LabMetaData type
    hed_lab_metadata = NWBGroupSpec(
        neurodata_type_def="HedLabMetaData",
        neurodata_type_inc="LabMetaData",
        name="hed_schema",
        doc="Extension type for storing a HED (Hierarchical Event Descriptor) schema in lab metadata",
        quantity="?",
        attributes=[
            NWBAttributeSpec(
                name="hed_schema_version",
                doc="The HED schema version(s) used in this NWB file, e.g., '8.4.0' or"
                + ' \'["score_2.1.0","lang_1.1.0"]\'.',
                dtype="text",
                required=True,
            ),
            NWBAttributeSpec(
                name="definitions",
                doc="A string containing one or more HED definitions.",
                dtype="text",
                required=False,
            ),
        ],
    )

    # Add all of new data types to this list
    new_data_types = [hed_lab_metadata, hed_tags, hed_value_vector]

    # export the spec to yaml files in the spec folder
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "spec"))
    export_spec(ns_builder, new_data_types, output_dir)
    print("Spec files generated. Please make sure to rerun `pip install .` to load the changes.")


if __name__ == "__main__":
    # usage: python create_extension_spec.py
    main()
